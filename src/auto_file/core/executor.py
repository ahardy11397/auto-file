"""Pipeline orchestrator and executor for the Auto-File system.

Integrates metadata detection, tool dispatching, content extraction,
multimodal document understanding, taxonomy routing, collision-safe naming,
atomic file movement with hash verification, and audit ledger tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from pathlib import Path
import shutil
from typing import TYPE_CHECKING, Any

from auto_file.core.detector import FileMetadata, detect_file_metadata
from auto_file.core.dispatcher import LayaDispatcher
from auto_file.core.extractors import get_extractor_for_tool
from auto_file.core.naming import compute_file_sha256, resolve_target_filename
from auto_file.core.router import TaxonomyRouter
from auto_file.core.taxonomy import load_taxonomy
from auto_file.core.understander import GemmaUnderstander, normalize_date_string

if TYPE_CHECKING:
    from auto_file.storage.audit import AuditLedger


logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of processing a file through the pipeline.

    Attributes:
        status: One of 'preview', 'moved', 'duplicate_skipped', 'failed'.
        original_path: Source file path.
        destination_path: Absolute or full destination path.
        proposed_relative_path: Relative path from target_root to destination_path.
        details: Dictionary of execution metadata (hashes, dates, entities, etc.).
        error_message: Optional error message if status is 'failed'.
    """

    status: str
    original_path: Path
    destination_path: Path
    proposed_relative_path: Path
    details: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.original_path, Path):
            self.original_path = Path(self.original_path)
        if not isinstance(self.destination_path, Path):
            self.destination_path = Path(self.destination_path)
        if not isinstance(self.proposed_relative_path, Path):
            self.proposed_relative_path = Path(self.proposed_relative_path)


class FilePipelineExecutor:
    """End-to-end file organization pipeline executor.

    Wires together:
    1. detect_file_metadata (hash, size, MIME type, timestamps)
    2. LayaDispatcher.dispatch_tool (tool selection)
    3. get_extractor_for_tool (content extraction)
    4. GemmaUnderstander.understand (date, description, entities, category, summary)
    5. TaxonomyRouter.resolve_destination (folder taxonomy path)
    6. resolve_target_filename (stem, duplicate detection, collision counter)
    7. Atomic file move & post-move verification (existence + hash check)
    8. AuditLedger.record_event (transaction logging for undo/rollback)
    """

    def __init__(
        self,
        target_root: Path | str,
        audit_ledger: AuditLedger | None = None,
        dispatcher: LayaDispatcher | None = None,
        understander: GemmaUnderstander | None = None,
        router: TaxonomyRouter | None = None,
        laya_model_path: Path | str | None = None,
        exact_spelling: bool = False,
        structure: Path | str | None = None,
        llm_server: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the pipeline executor.

        Args:
            target_root: Destination root directory for organized files.
            audit_ledger: Optional SQLite audit ledger for rollback recording.
            dispatcher: Optional custom extractor tool dispatcher.
            understander: Optional custom document understanding model.
            router: Optional custom taxonomy folder router.
            laya_model_path: Optional path to Laya ONNX decision model weights.
            exact_spelling: If True, uses verbatim spelling from FOLDER_STRUCTURE.md.
            structure: Optional path to a YAML folder-structure file. When
                given, routing follows that file instead of the built-in
                defaults (ignored when a custom router is supplied).
            llm_server: Optional on-demand llama.cpp server config (keys:
                binary, model, mmproj, port, idle_seconds). Spawns the server
                only while documents are being understood and stops it after
                idling — no standing network service.
        """
        self.target_root = Path(target_root)
        self.audit_ledger = audit_ledger
        self.dispatcher = dispatcher or LayaDispatcher(model_path=laya_model_path)
        self.understander = understander or GemmaUnderstander(llama_server=llm_server)
        if router is not None:
            self.router = router
        elif structure is not None:
            self.router = TaxonomyRouter(taxonomy=load_taxonomy(structure))
        else:
            self.router = TaxonomyRouter(model_path=laya_model_path, exact_spelling=exact_spelling)

    def _needs_review_result(
        self,
        orig_path: Path,
        metadata: Any,
        tool_name: str,
        reason: str,
        dry_run: bool,
        run_id: str | None,
    ) -> PipelineResult:
        """Build a needs_review result: the file stays untouched in place."""
        details: dict[str, Any] = {
            "mime_type": metadata.mime_type,
            "sha256": metadata.sha256,
            "tool_selected": tool_name,
            "date_value": metadata.mtime.strftime("%Y-%m-%d"),
            "reason": reason,
        }
        if not dry_run and self.audit_ledger is not None:
            active_run_id = run_id
            need_finish = False
            if active_run_id is None:
                active_run_id = self.audit_ledger.start_run(
                    mode="cli_single",
                    source_root=orig_path,
                    target_root=self.target_root,
                )
                need_finish = True
            event_id = self.audit_ledger.record_event(
                run_id=active_run_id,
                original_path=orig_path,
                destination_path=orig_path,
                sha256=metadata.sha256,
                file_size=metadata.size_bytes,
                date_source="none",
                date_value="",
                description="needs_review",
                laya_tool_selected=tool_name,
                laya_category_selected=reason,
                status="needs_review",
            )
            details["audit_event_id"] = event_id
            details["audit_run_id"] = active_run_id
            if need_finish:
                self.audit_ledger.finish_run(active_run_id)

        return PipelineResult(
            status="needs_review",
            original_path=orig_path,
            destination_path=orig_path,
            proposed_relative_path=Path("_needs_review") / orig_path.name,
            details=details,
        )

    def process_file(
        self,
        file_path: Path | str,
        dry_run: bool = False,
        run_id: str | None = None,
        raise_on_error: bool = False,
    ) -> PipelineResult:
        """Process a single file through the full organization pipeline.

        Args:
            file_path: Path to the source file to organize.
            dry_run: If True, calculates destination and returns 'preview'
                without moving the file or modifying disk.
            run_id: Optional existing run_id to group audit events under.
            raise_on_error: If True, raises exceptions encountered during processing;
                if False, returns PipelineResult with status='failed'.

        Returns:
            PipelineResult indicating outcome and metadata.
        """
        orig_path = Path(file_path)
        file_moved = False
        resolved: Any = None

        try:
            if not orig_path.exists():
                raise FileNotFoundError(f"Source file not found: {orig_path}")
            if not orig_path.is_file():
                raise ValueError(f"Source path is not a regular file: {orig_path}")

            # 1. Metadata inspection
            metadata = detect_file_metadata(orig_path)

            # 2. Tool dispatch
            tool_name = self.dispatcher.dispatch_tool(metadata)

            # 3. Content extraction
            extractor = get_extractor_for_tool(tool_name)
            extracted = extractor.extract(metadata)

            # 4. Multimodal semantic understanding
            understanding = self.understander.understand(extracted, filename_hint=orig_path.name)

            # 4.5 Understanding gate: when the understander could not
            # confidently read the document, leave it untouched in the inbox
            # for manual review instead of renaming it into a generic folder.
            if not getattr(understanding, "understood", True):
                return self._needs_review_result(
                    orig_path, metadata, tool_name, "insufficient_understanding", dry_run, run_id
                )

            # 5. Destination routing — LLM picks from the real folder tree
            # when available; the keyword router is the no-LLM fallback. An
            # LLM that cannot pick a fitting folder gates to needs_review
            # rather than guessing.
            if self.understander.has_llm_routing:
                status, chosen = self.understander.route_with_llama(
                    filename=orig_path.name,
                    summary=understanding.summary,
                    description=understanding.file_description,
                    content_date=understanding.content_date,
                    folder_choices=self.router.taxonomy.all_paths(),
                )
                if status == "ok":
                    canonical = self.router.taxonomy.is_valid_folder(chosen or "")
                    if canonical is None:
                        return self._needs_review_result(
                            orig_path, metadata, tool_name, "llm_invalid_folder", dry_run, run_id
                        )
                    relative_folder = Path(canonical)
                elif status == "unreachable":
                    relative_folder = self.router.resolve_destination(
                        entities=understanding.detected_entities,
                        category_hint=understanding.category_hint,
                        summary=understanding.summary,
                        filename_hint=orig_path.name,
                    )
                else:
                    return self._needs_review_result(
                        orig_path, metadata, tool_name, "llm_could_not_route", dry_run, run_id
                    )
            else:
                relative_folder = self.router.resolve_destination(
                    entities=understanding.detected_entities,
                    category_hint=understanding.category_hint,
                    summary=understanding.summary,
                    filename_hint=orig_path.name,
                )

            # 6. Date precedence: content date if present, fallback to filesystem mtime YYYY-MM-DD
            if understanding.content_date and understanding.content_date.strip():
                date_val = understanding.content_date.strip()
                if extracted.exif_date and date_val == normalize_date_string(extracted.exif_date):
                    date_src = "exif"
                else:
                    date_src = "content"
            else:
                date_val = metadata.mtime.strftime("%Y-%m-%d")
                date_src = "filesystem"

            # 7. Destination and filename resolution
            target_dir = self.target_root / relative_folder
            resolved = resolve_target_filename(
                date_str=date_val,
                description=understanding.file_description,
                extension=metadata.extension,
                destination_dir=target_dir,
                file_sha256=metadata.sha256,
            )

            try:
                proposed_rel = resolved.target_path.relative_to(self.target_root)
            except ValueError:
                proposed_rel = relative_folder / resolved.target_path.name

            details: dict[str, Any] = {
                "mime_type": metadata.mime_type,
                "extension": metadata.extension,
                "size_bytes": metadata.size_bytes,
                "sha256": metadata.sha256,
                "tool_selected": tool_name,
                "date_source": date_src,
                "date_value": date_val,
                "description": understanding.file_description,
                "category_hint": understanding.category_hint,
                "detected_entities": understanding.detected_entities,
                "summary": understanding.summary,
                "relative_folder": str(relative_folder),
                "is_duplicate": resolved.is_duplicate,
                "dry_run": dry_run,
            }

            # Case 1: Duplicate detection - skip moving if identical SHA-256 already exists
            if resolved.is_duplicate:
                if not dry_run and self.audit_ledger is not None:
                    active_run_id = run_id
                    need_finish = False
                    if active_run_id is None:
                        active_run_id = self.audit_ledger.start_run(
                            mode="cli_single",
                            source_root=orig_path,
                            target_root=self.target_root,
                        )
                        need_finish = True

                    event_id = self.audit_ledger.record_event(
                        run_id=active_run_id,
                        original_path=orig_path,
                        destination_path=resolved.target_path,
                        sha256=metadata.sha256,
                        file_size=metadata.size_bytes,
                        date_source=date_src,
                        date_value=date_val,
                        description=understanding.file_description,
                        laya_tool_selected=tool_name,
                        laya_category_selected=str(relative_folder),
                        status="duplicate_skipped",
                    )
                    details["audit_event_id"] = event_id
                    details["audit_run_id"] = active_run_id
                    if need_finish:
                        self.audit_ledger.finish_run(active_run_id)

                return PipelineResult(
                    status="duplicate_skipped",
                    original_path=orig_path,
                    destination_path=resolved.target_path,
                    proposed_relative_path=proposed_rel,
                    details=details,
                )

            # Case 2: Dry run - preview destination without moving
            if dry_run:
                return PipelineResult(
                    status="preview",
                    original_path=orig_path,
                    destination_path=resolved.target_path,
                    proposed_relative_path=proposed_rel,
                    details=details,
                )

            # Case 3: Live move - create parents, atomic move, verify, and record audit event
            resolved.target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(orig_path), str(resolved.target_path))
            file_moved = True

            # Verification: target exists and SHA-256 matches
            if not resolved.target_path.is_file():
                raise RuntimeError(
                    f"Move verification failed: destination file missing at {resolved.target_path}"
                )

            verified_sha = compute_file_sha256(resolved.target_path)
            if verified_sha.lower() != metadata.sha256.lower():
                raise RuntimeError(
                    f"Move verification failed: SHA-256 mismatch at {resolved.target_path} "
                    f"(expected {metadata.sha256}, got {verified_sha})"
                )

            # Audit recording
            if self.audit_ledger is not None:
                active_run_id = run_id
                need_finish = False
                if active_run_id is None:
                    active_run_id = self.audit_ledger.start_run(
                        mode="cli_single",
                        source_root=orig_path,
                        target_root=self.target_root,
                    )
                    need_finish = True

                event_id = self.audit_ledger.record_event(
                    run_id=active_run_id,
                    original_path=orig_path,
                    destination_path=resolved.target_path,
                    sha256=metadata.sha256,
                    file_size=metadata.size_bytes,
                    date_source=date_src,
                    date_value=date_val,
                    description=understanding.file_description,
                    laya_tool_selected=tool_name,
                    laya_category_selected=str(relative_folder),
                    status="moved",
                )
                details["audit_event_id"] = event_id
                details["audit_run_id"] = active_run_id
                if need_finish:
                    self.audit_ledger.finish_run(active_run_id)

            return PipelineResult(
                status="moved",
                original_path=orig_path,
                destination_path=resolved.target_path,
                proposed_relative_path=proposed_rel,
                details=details,
            )

        except Exception as exc:
            if raise_on_error:
                raise

            logger.error("Pipeline execution failed for %s: %s", orig_path, exc)
            dest_for_failure = (
                resolved.target_path
                if (file_moved and resolved is not None and getattr(resolved, "target_path", None) is not None)
                else orig_path
            )
            if not dry_run and self.audit_ledger is not None:
                try:
                    active_run_id = run_id
                    need_finish = False
                    if active_run_id is None:
                        active_run_id = self.audit_ledger.start_run(
                            mode="cli_single",
                            source_root=orig_path,
                            target_root=self.target_root,
                        )
                        need_finish = True

                    self.audit_ledger.record_event(
                        run_id=active_run_id,
                        original_path=orig_path,
                        destination_path=dest_for_failure,
                        sha256="",
                        file_size=0,
                        date_source="error",
                        date_value="",
                        description="",
                        laya_tool_selected="error",
                        laya_category_selected="error",
                        status="failed",
                        error_message=str(exc),
                    )
                    if need_finish:
                        self.audit_ledger.finish_run(active_run_id)
                except Exception as audit_exc:
                    logger.warning("Failed to record error event in audit ledger: %s", audit_exc)

            return PipelineResult(
                status="failed",
                original_path=orig_path,
                destination_path=dest_for_failure,
                proposed_relative_path=Path(""),
                details={"error": str(exc)},
                error_message=str(exc),
            )

    def process_directory(
        self,
        source_dir: Path | str,
        dry_run: bool = False,
        recursive: bool = False,
        run_id: str | None = None,
    ) -> list[PipelineResult]:
        """Process a directory of files in batch mode.

        Args:
            source_dir: Directory path containing files to organize.
            dry_run: If True, previews proposed file movements without modifying disk.
            recursive: If True, traverses subdirectories recursively.
            run_id: Optional existing run_id to group audit events under.

        Returns:
            List of PipelineResult objects for each file processed.
        """
        source_path = Path(source_dir)
        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_path}")
        if not source_path.is_dir():
            raise NotADirectoryError(f"Source path is not a directory: {source_path}")

        # Discover files
        if recursive:
            candidates = [p for p in source_path.rglob("*") if p.is_file()]
        else:
            candidates = [p for p in source_path.iterdir() if p.is_file()]

        # Filter out hidden files / dotfiles (e.g. .DS_Store, .git)
        files = sorted(
            [
                p
                for p in candidates
                if not p.name.startswith(".")
                and not any(part.startswith(".") for part in p.relative_to(source_path).parts)
            ],
            key=lambda p: str(p),
        )

        # Manage audit run lifecycle for batch mode
        active_run_id = run_id
        own_run = False
        if not dry_run and self.audit_ledger is not None:
            if active_run_id is None:
                active_run_id = self.audit_ledger.start_run(
                    mode="cli_batch",
                    source_root=source_path,
                    target_root=self.target_root,
                )
                own_run = True

        results: list[PipelineResult] = []
        for file_path in files:
            res = self.process_file(
                file_path=file_path,
                dry_run=dry_run,
                run_id=active_run_id,
            )
            results.append(res)

        if own_run and self.audit_ledger is not None and active_run_id is not None:
            self.audit_ledger.finish_run(active_run_id)

        return results
