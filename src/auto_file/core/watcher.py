"""Background folder watcher daemon for automatic file organization.

Monitors an inbox folder for incoming files, applies stability and debounce
checks to ensure complete writes, and automatically invokes FilePipelineExecutor.
"""

from __future__ import annotations

import logging
from pathlib import Path
import threading
import time
from typing import Callable, Optional

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    FileSystemMovedEvent,
)
from watchdog.observers import Observer

from auto_file.core.executor import FilePipelineExecutor, PipelineResult

logger = logging.getLogger(__name__)

# Temporary download / partial extensions to ignore
IGNORED_EXTENSIONS = {".tmp", ".part", ".crdownload"}


class _InboxEventHandler(FileSystemEventHandler):
    """Event handler that forwards file creation, modification, and rename events to FolderWatcher."""

    def __init__(self, watcher: FolderWatcher) -> None:
        super().__init__()
        self.watcher = watcher

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.watcher._queue_file(Path(event.src_path))

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.watcher._queue_file(Path(event.src_path))

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        if not event.is_directory:
            self.watcher._remove_file(Path(event.src_path))
            self.watcher._queue_file(Path(event.dest_path))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self.watcher._remove_file(Path(event.src_path))


class FolderWatcher:
    """Daemon that monitors an inbox directory and organizes incoming files.

    Features:
    - Debounce timer: wait for debounce_seconds before attempting to process.
    - File stability check: verifies file size does not fluctuate before processing.
    - Readability check: ensures file is completely flushed and not locked by writer.
    - Filter: ignores hidden files (.*) and temporary extensions (.tmp, .part, .crdownload).
    - Recursive: optionally watches subdirectories.
    """

    def __init__(
        self,
        inbox_dir: Path | str,
        executor: FilePipelineExecutor,
        debounce_seconds: float = 2.0,
        recursive: bool = False,
        on_processed: Optional[Callable[[PipelineResult], None]] = None,
    ) -> None:
        """Initialize FolderWatcher.

        Args:
            inbox_dir: Path to inbox directory to monitor.
            executor: Configured FilePipelineExecutor instance.
            debounce_seconds: Seconds to wait after last modification before processing.
            recursive: If True, recursively monitors subdirectories.
            on_processed: Optional callback invoked with PipelineResult after file processing.
        """
        self.inbox_dir = Path(inbox_dir).resolve()
        if not self.inbox_dir.exists():
            raise FileNotFoundError(f"Inbox directory does not exist: {self.inbox_dir}")
        if not self.inbox_dir.is_dir():
            raise NotADirectoryError(f"Inbox path is not a directory: {self.inbox_dir}")

        self.executor = executor
        self.debounce_seconds = float(debounce_seconds)
        self.recursive = bool(recursive)
        self.on_processed = on_processed

        self._observer: Optional[Observer] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pending: dict[Path, tuple[float, int]] = {}
        self._lock = threading.Lock()
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Return True if watcher is actively running."""
        return self._is_running and self._observer is not None and self._observer.is_alive()

    def is_ignored(self, path: Path) -> bool:
        """Check whether a path should be ignored (hidden file or temporary extension)."""
        # 1. Ignored extensions
        if path.suffix.lower() in IGNORED_EXTENSIONS:
            return True

        # 2. Hidden files or directories (.something)
        try:
            rel = path.relative_to(self.inbox_dir)
            if any(part.startswith(".") for part in rel.parts):
                return True
        except ValueError:
            if any(part.startswith(".") for part in path.parts):
                return True

        # 3. Inside executor target_root (prevent loop when target_root is inside inbox_dir)
        if hasattr(self.executor, "target_root"):
            try:
                target_root_resolved = Path(self.executor.target_root).resolve()
                if path.is_relative_to(target_root_resolved):
                    return True
            except (OSError, ValueError):
                pass

        return False

    def _queue_file(self, path: Path) -> None:
        """Queue or reset debounce timer for a file path."""
        try:
            resolved_path = path.resolve()
        except OSError:
            return

        # Boundary check: ensure path is inside inbox_dir
        if not resolved_path.is_relative_to(self.inbox_dir):
            return

        # If target_root is inside inbox_dir, ignore files inside it
        if hasattr(self.executor, "target_root"):
            try:
                target_root_resolved = Path(self.executor.target_root).resolve()
                if resolved_path.is_relative_to(target_root_resolved):
                    return
            except (OSError, ValueError):
                pass

        if self.is_ignored(resolved_path):
            return

        if not self.recursive:
            try:
                if resolved_path.parent != self.inbox_dir:
                    return
            except Exception:
                return

        if not resolved_path.exists() or not resolved_path.is_file():
            return

        try:
            current_size = resolved_path.stat().st_size
        except OSError:
            current_size = -1

        target_time = time.time() + self.debounce_seconds
        with self._lock:
            self._pending[resolved_path] = (target_time, current_size)

    def _remove_file(self, path: Path) -> None:
        """Remove a file from pending queue (e.g. deleted or moved away)."""
        try:
            resolved_path = path.resolve()
        except OSError:
            resolved_path = path

        with self._lock:
            self._pending.pop(resolved_path, None)

    def _worker_loop(self) -> None:
        """Worker thread loop checking pending files for stability and triggering executor."""
        while not self._stop_event.is_set():
            now = time.time()
            ready_files: list[Path] = []

            with self._lock:
                for path, (target_time, last_size) in list(self._pending.items()):
                    if now < target_time:
                        continue

                    # If file disappeared or became invalid
                    if not path.is_file() or self.is_ignored(path):
                        self._pending.pop(path, None)
                        continue

                    # Stability check: compare current size with last recorded size
                    try:
                        current_size = path.stat().st_size
                    except OSError:
                        # Transient lock or file access error
                        self._pending[path] = (now + min(self.debounce_seconds, 0.5), last_size)
                        continue

                    if current_size != last_size:
                        # File is still being actively written
                        self._pending[path] = (now + self.debounce_seconds, current_size)
                        continue

                    # Readability check: verify file can be opened and read without lock contention
                    try:
                        with open(path, "rb") as f:
                            f.read(1024)
                    except OSError:
                        # Writer may hold exclusive lock (e.g., ongoing copy/download)
                        self._pending[path] = (now + min(self.debounce_seconds, 0.5), current_size)
                        continue

                    # File is stable and readable!
                    self._pending.pop(path, None)
                    ready_files.append(path)

            for path in ready_files:
                if self._stop_event.is_set():
                    break
                self._process_file_safe(path)

            self._stop_event.wait(timeout=0.05)

    def _process_file_safe(self, path: Path) -> Optional[PipelineResult]:
        """Safely process a single file through the pipeline executor."""
        if not path.is_file():
            return None
        try:
            result = self.executor.process_file(path)
            if self.on_processed:
                try:
                    self.on_processed(result)
                except Exception as exc:
                    logger.warning("Error in on_processed callback: %s", exc)
            return result
        except Exception as exc:
            logger.exception("Failed to process file %s: %s", path, exc)
            return None

    def start(self) -> None:
        """Start watchdog observer and background stability worker."""
        if self._is_running:
            return

        if not self.inbox_dir.exists():
            raise FileNotFoundError(f"Inbox directory does not exist: {self.inbox_dir}")
        if not self.inbox_dir.is_dir():
            raise NotADirectoryError(f"Inbox path is not a directory: {self.inbox_dir}")

        self._stop_event.clear()
        self._observer = Observer()
        handler = _InboxEventHandler(self)
        self._observer.schedule(handler, str(self.inbox_dir), recursive=self.recursive)
        self._observer.start()

        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name=f"FolderWatcherWorker-{self.inbox_dir.name}",
            daemon=True,
        )
        self._worker_thread.start()
        self._is_running = True

    def stop(self, timeout: float = 5.0) -> None:
        """Stop watchdog observer and worker thread cleanly."""
        if not self._is_running:
            return

        self._is_running = False
        self._stop_event.set()

        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=timeout)
            except Exception as exc:
                logger.warning("Error stopping watchdog observer: %s", exc)
            finally:
                self._observer = None

        if self._worker_thread is not None:
            try:
                self._worker_thread.join(timeout=timeout)
            except Exception as exc:
                logger.warning("Error joining worker thread: %s", exc)
            finally:
                self._worker_thread = None

    def __enter__(self) -> FolderWatcher:
        self.start()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.stop()
