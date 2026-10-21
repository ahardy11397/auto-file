"""SQLite Audit Ledger & Rollback Engine for Auto-File.

Provides transactional tracking of processing runs and file operations,
allowing safe, verified rollback of file movements in reverse chronological order.
"""

from datetime import datetime, timezone
from pathlib import Path
import shutil
import sqlite3
import threading
from typing import Any
import uuid

from auto_file.core.naming import compute_file_sha256


class AuditError(Exception):
    """Base exception for audit ledger and rollback operations."""


class RollbackError(AuditError):
    """Exception raised when a rollback operation fails."""


class RollbackVerificationError(RollbackError):
    """Exception raised when target file hash does not match recorded SHA-256."""


class RollbackMissingFileError(RollbackError, FileNotFoundError):
    """Exception raised when destination file to roll back is missing from disk."""


class RollbackCollisionError(RollbackError):
    """Exception raised when original destination path already exists during rollback."""


RollbackTargetExistsError = RollbackCollisionError


class AuditLedger:
    """Manages the SQLite audit ledger for pipeline runs and file movement events."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT NOT NULL,
        completed_at TEXT,
        mode TEXT NOT NULL,
        source_root TEXT NOT NULL,
        target_root TEXT NOT NULL,
        total_files INTEGER DEFAULT 0,
        successful_files INTEGER DEFAULT 0,
        failed_files INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS file_events (
        id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        timestamp TEXT NOT NULL,
        original_path TEXT NOT NULL,
        destination_path TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        date_source TEXT NOT NULL,
        date_value TEXT NOT NULL,
        description TEXT NOT NULL,
        laya_tool_selected TEXT NOT NULL,
        laya_category_selected TEXT NOT NULL,
        status TEXT NOT NULL,
        error_message TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_file_events_run_id ON file_events(run_id);
    CREATE INDEX IF NOT EXISTS idx_file_events_status ON file_events(status);
    CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
    """

    def __init__(self, db_path: Path | str = "audit.db") -> None:
        """Initialize SQLite database connection and verify table schema.

        Args:
            db_path: Path to the SQLite database file, or ':memory:'.
        """
        self.db_path = db_path if str(db_path) == ":memory:" else Path(db_path)
        self._lock = threading.RLock()

        if str(self.db_path) != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        with self._lock:
            self._conn.execute("PRAGMA foreign_keys = ON;")
            self._conn.execute("PRAGMA busy_timeout = 5000;")
            if str(self.db_path) != ":memory:":
                try:
                    self._conn.execute("PRAGMA journal_mode = WAL;")
                except sqlite3.DatabaseError:
                    pass
            self._conn.executescript(self.SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        """Close the SQLite database connection."""
        with self._lock:
            if self._conn:
                self._conn.close()

    def __enter__(self) -> "AuditLedger":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def start_run(
        self,
        mode: str,
        source_root: Path | str,
        target_root: Path | str,
        *,
        run_id: str | None = None,
    ) -> str:
        """Create a new run entry in the audit ledger.

        Args:
            mode: Operational mode ('cli_single', 'cli_batch', 'watch_daemon').
            source_root: Source directory or file path.
            target_root: Target destination root directory.
            run_id: Optional explicit run identifier (generates UUID4 if omitted).

        Returns:
            The unique run_id string.
        """
        active_run_id = run_id or uuid.uuid4().hex
        started_at = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._conn.execute(
                """
                INSERT INTO runs (
                    run_id, started_at, completed_at, mode,
                    source_root, target_root, total_files,
                    successful_files, failed_files
                ) VALUES (?, ?, NULL, ?, ?, ?, 0, 0, 0)
                """,
                (
                    active_run_id,
                    started_at,
                    mode,
                    str(source_root),
                    str(target_root),
                ),
            )
            self._conn.commit()

        return active_run_id

    def finish_run(
        self,
        run_id: str,
        total_files: int = 0,
        successful_files: int = 0,
        failed_files: int = 0,
    ) -> None:
        """Mark a run as completed and update file count statistics.

        If count arguments are all 0, counts are automatically aggregated from
        recorded file_events for this run.

        Args:
            run_id: Run identifier to update.
            total_files: Total number of files processed.
            successful_files: Number of files successfully moved or skipped.
                Files left for review (``needs_review``) count as successful:
                they were handled safely, without a move.
            failed_files: Number of failed files.
        """
        completed_at = datetime.now(timezone.utc).isoformat()

        with self._lock:
            # Auto-aggregate from file_events if defaults were passed
            if total_files == 0 and successful_files == 0 and failed_files == 0:
                cur = self._conn.execute(
                    """
                    SELECT
                        COUNT(*),
                        SUM(CASE WHEN status IN ('moved', 'duplicate_skipped', 'needs_review')
                                 THEN 1 ELSE 0 END),
                        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)
                    FROM file_events
                    WHERE run_id = ?
                    """,
                    (run_id,),
                )
                row = cur.fetchone()
                if row and row[0] > 0:
                    total_files = int(row[0])
                    successful_files = int(row[1] or 0)
                    failed_files = int(row[2] or 0)

            self._conn.execute(
                """
                UPDATE runs
                SET completed_at = ?,
                    total_files = ?,
                    successful_files = ?,
                    failed_files = ?
                WHERE run_id = ?
                """,
                (
                    completed_at,
                    total_files,
                    successful_files,
                    failed_files,
                    run_id,
                ),
            )
            self._conn.commit()

    def record_event(
        self,
        run_id: str,
        original_path: Path | str,
        destination_path: Path | str,
        sha256: str,
        file_size: int,
        date_source: str,
        date_value: str,
        description: str,
        laya_tool_selected: str,
        laya_category_selected: str,
        status: str = "moved",
        error_message: str | None = None,
        *,
        event_id: str | None = None,
        timestamp: str | None = None,
    ) -> str:
        """Record an individual file processing or movement event.

        Args:
            run_id: Associated run identifier.
            original_path: File path before processing.
            destination_path: Target destination path.
            sha256: SHA-256 digest of the file.
            file_size: File size in bytes.
            date_source: Extraction source of date ('content', 'exif', 'filesystem').
            date_value: Normalized date string (e.g. YYYY-MM-DD).
            description: Sanitized description slug.
            laya_tool_selected: Tool selected by dispatcher.
            laya_category_selected: Target taxonomy category selected.
            status: Event status ('moved', 'rolled_back', 'failed', 'duplicate_skipped').
            error_message: Optional error message if failed.
            event_id: Optional explicit event identifier.
            timestamp: Optional ISO 8601 timestamp.

        Returns:
            The event_id string.
        """
        active_event_id = event_id or uuid.uuid4().hex
        active_timestamp = timestamp or datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._conn.execute(
                """
                INSERT INTO file_events (
                    id, run_id, timestamp, original_path,
                    destination_path, sha256, file_size,
                    date_source, date_value, description,
                    laya_tool_selected, laya_category_selected,
                    status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    active_event_id,
                    run_id,
                    active_timestamp,
                    str(original_path),
                    str(destination_path),
                    sha256,
                    file_size,
                    date_source,
                    date_value,
                    description,
                    laya_tool_selected,
                    laya_category_selected,
                    status,
                    error_message,
                ),
            )
            self._conn.commit()

        return active_event_id

    def get_history(self, limit: int = 25) -> list[dict[str, Any]]:
        """Retrieve recent run history in reverse chronological order.

        Args:
            limit: Maximum number of run records to return.

        Returns:
            List of dictionaries containing run metadata.
        """
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT run_id, started_at, completed_at, mode,
                       source_root, target_root, total_files,
                       successful_files, failed_files
                FROM runs
                ORDER BY started_at DESC, rowid DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_recent_events(self, limit: int = 25) -> list[dict[str, Any]]:
        """Retrieve recent file events across all runs, newest first.

        Args:
            limit: Maximum number of event records to return.

        Returns:
            List of file event dictionaries.
        """
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT *
                FROM file_events
                ORDER BY timestamp DESC, rowid DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Fetch details for a specific run.

        Args:
            run_id: Run identifier.

        Returns:
            Dictionary with run details or None if not found.
        """
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT run_id, started_at, completed_at, mode,
                       source_root, target_root, total_files,
                       successful_files, failed_files
                FROM runs
                WHERE run_id = ?
                """,
                (run_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    def get_events_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """Fetch all file events associated with a run.

        Args:
            run_id: Run identifier.

        Returns:
            List of file event dictionaries.
        """
        with self._lock:
            cur = self._conn.execute(
                """
                SELECT *
                FROM file_events
                WHERE run_id = ?
                ORDER BY timestamp ASC, rowid ASC
                """,
                (run_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def rollback_run(
        self,
        run_id: str | None = None,
        *,
        verify_hash: bool = True,
        strict: bool = True,
    ) -> list[dict[str, Any]]:
        """Roll back moved files from a run in reverse chronological order.

        Safety verification:
        1. Destination file must exist.
        2. Destination file SHA-256 must match the recorded digest before moving back.
        If verification fails or destination is missing:
        - If strict=True: raises RollbackError / RollbackMissingFileError / RollbackVerificationError.
        - If strict=False: flags event as skipped without destroying user data.

        Args:
            run_id: Specific run to roll back. If None, targets the latest run with moved files.
            verify_hash: Whether to verify destination file's SHA-256 before restoring.
            strict: If True, raises exceptions on validation failures; if False, flags as skipped.

        Returns:
            List of event dictionaries that were processed or updated during rollback.
        """
        with self._lock:
            target_run_id = run_id

            if target_run_id is None:
                # Find latest run that has moved files
                cur = self._conn.execute(
                    """
                    SELECT r.run_id
                    FROM runs r
                    JOIN file_events e ON r.run_id = e.run_id
                    WHERE e.status = 'moved'
                    ORDER BY r.started_at DESC, r.rowid DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                if row:
                    target_run_id = row[0]
                else:
                    # Fallback to latest run overall
                    cur = self._conn.execute(
                        "SELECT run_id FROM runs ORDER BY started_at DESC, rowid DESC LIMIT 1"
                    )
                    row = cur.fetchone()
                    if row:
                        target_run_id = row[0]
                    else:
                        return []

            # Retrieve all 'moved' events in reverse chronological order
            cur = self._conn.execute(
                """
                SELECT *
                FROM file_events
                WHERE run_id = ? AND status = 'moved'
                ORDER BY timestamp DESC, rowid DESC
                """,
                (target_run_id,),
            )
            events = [dict(row) for row in cur.fetchall()]

            undone_events: list[dict[str, Any]] = []

            for event in events:
                dest_path = Path(event["destination_path"])
                orig_path = Path(event["original_path"])
                recorded_sha = event["sha256"]

                # 1. Verify destination file exists
                if not dest_path.is_file():
                    msg = f"Rollback target file does not exist: {dest_path}"
                    if strict:
                        raise RollbackMissingFileError(msg)
                    event["status"] = "skipped"
                    event["error_message"] = msg
                    self._conn.execute(
                        "UPDATE file_events SET error_message = ? WHERE id = ?",
                        (msg, event["id"]),
                    )
                    self._conn.commit()
                    undone_events.append(event)
                    continue

                # 2. Verify SHA-256 match if hash verification is active and recorded hash is standard hex
                is_standard_hex_sha256 = (
                    len(recorded_sha) == 64
                    and all(c in "0123456789abcdefABCDEF" for c in recorded_sha)
                )

                if verify_hash and is_standard_hex_sha256:
                    actual_sha = compute_file_sha256(dest_path)
                    if actual_sha.lower() != recorded_sha.lower():
                        msg = (
                            f"Rollback SHA-256 verification failed for {dest_path}: "
                            f"expected {recorded_sha}, got {actual_sha}"
                        )
                        if strict:
                            raise RollbackVerificationError(msg)
                        event["status"] = "skipped"
                        event["error_message"] = msg
                        self._conn.execute(
                            "UPDATE file_events SET error_message = ? WHERE id = ?",
                            (msg, event["id"]),
                        )
                        self._conn.commit()
                        undone_events.append(event)
                        continue

                # 3. Verify original destination path does not already exist
                if orig_path.exists():
                    msg = f"Rollback target already exists: {orig_path}"
                    if strict:
                        raise RollbackCollisionError(msg)
                    event["status"] = "skipped"
                    event["error_message"] = msg
                    self._conn.execute(
                        "UPDATE file_events SET error_message = ? WHERE id = ?",
                        (msg, event["id"]),
                    )
                    self._conn.commit()
                    undone_events.append(event)
                    continue

                # 4. Restore file to original_path
                orig_path.parent.mkdir(parents=True, exist_ok=True)
                if dest_path.resolve() != orig_path.resolve():
                    shutil.move(str(dest_path), str(orig_path))

                # 5. Update status in database
                self._conn.execute(
                    "UPDATE file_events SET status = 'rolled_back' WHERE id = ?",
                    (event["id"],),
                )
                self._conn.commit()

                event["status"] = "rolled_back"
                undone_events.append(event)

            return undone_events
