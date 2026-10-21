"""Comprehensive tests for pipeline orchestrator and executor."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from auto_file.core.executor import FilePipelineExecutor, PipelineResult
from auto_file.core.extractors.base import ExtractedContent
from auto_file.core.naming import compute_file_sha256
from auto_file.core.understander import GemmaUnderstander, UnderstandingResult
from auto_file.storage.audit import AuditLedger


# ==============================================================================
# Basic Integration Tests (Brief)
# ==============================================================================


def test_pipeline_dry_run_does_not_move_file(tmp_path: Path):
    """Verify dry-run returns preview status and leaves filesystem unchanged."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "statement.txt"
    test_file.write_text("Bank statement for Chase account", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    result = executor.process_file(test_file, dry_run=True)
    assert isinstance(result, PipelineResult)
    assert result.status == "preview"
    assert test_file.exists()
    assert not (target_dir / result.proposed_relative_path).exists()


def test_pipeline_live_move(tmp_path: Path):
    """Verify live run atomically moves file to target taxonomy and removes source."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "statement.txt"
    test_file.write_text("Bank statement for Chase account", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    result = executor.process_file(test_file, dry_run=False)
    assert isinstance(result, PipelineResult)
    assert result.status == "moved"
    assert not test_file.exists()
    assert (target_dir / result.proposed_relative_path).exists()
    assert result.destination_path.is_file()


# ==============================================================================
# Duplicate Detection and Collision Tests
# ==============================================================================


def test_pipeline_duplicate_file_skipped(tmp_path: Path):
    """Verify that a file matching SHA-256 of an existing target is skipped."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    # Move first file
    file1 = source_dir / "statement1.txt"
    file1.write_text("Bank statement for Chase account on 2026-03-01", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    res1 = executor.process_file(file1, dry_run=False)
    assert res1.status == "moved"

    # Second file with identical content
    file2 = source_dir / "statement2.txt"
    file2.write_text("Bank statement for Chase account on 2026-03-01", encoding="utf-8")

    res2 = executor.process_file(file2, dry_run=False)
    assert res2.status == "duplicate_skipped"
    # Second file remains in inbox untouched
    assert file2.exists()
    assert res2.details["is_duplicate"] is True

    # Audit ledger tracks duplicate_skipped event
    events = ledger.get_events_for_run(res2.details["audit_run_id"])
    assert any(e["status"] == "duplicate_skipped" for e in events)


def test_pipeline_duplicate_file_dry_run(tmp_path: Path):
    """Verify dry run on a duplicate file returns duplicate_skipped without moving."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    file1 = source_dir / "statement1.txt"
    file1.write_text("Bank statement for Chase account on 2026-03-01", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    res1 = executor.process_file(file1, dry_run=False)
    assert res1.status == "moved"

    file2 = source_dir / "statement2.txt"
    file2.write_text("Bank statement for Chase account on 2026-03-01", encoding="utf-8")

    res2 = executor.process_file(file2, dry_run=True)
    assert res2.status == "duplicate_skipped"
    assert file2.exists()


def test_pipeline_collision_different_content(tmp_path: Path):
    """Verify that different files resolving to the same stem get incremented suffixes (_1, _2)."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    file1 = source_dir / "statement_a.txt"
    file1.write_text("Bank statement for Chase account on 2026-03-01 (version A)", encoding="utf-8")

    file2 = source_dir / "statement_b.txt"
    file2.write_text("Bank statement for Chase account on 2026-03-01 (version B)", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    res1 = executor.process_file(file1, dry_run=False)
    res2 = executor.process_file(file2, dry_run=False)

    assert res1.status == "moved"
    assert res2.status == "moved"
    assert res1.destination_path != res2.destination_path
    assert res2.destination_path.stem.endswith("_1")
    assert res1.destination_path.exists()
    assert res2.destination_path.exists()
    assert res1.destination_path.read_text(encoding="utf-8") != res2.destination_path.read_text(encoding="utf-8")


# ==============================================================================
# Date Precedence Tests
# ==============================================================================


def test_pipeline_date_precedence_content_date(tmp_path: Path):
    """Verify that document content date takes precedence over filesystem mtime."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "receipt.txt"
    test_file.write_text("Receipt from Home Depot on 2024-05-18 for $45.00", encoding="utf-8")

    executor = FilePipelineExecutor(target_root=target_dir)
    result = executor.process_file(test_file, dry_run=True)

    assert result.status == "preview"
    assert result.details["date_source"] == "content"
    assert result.details["date_value"] == "2024-05-18"
    assert result.proposed_relative_path.name.startswith("2024-05-18_")


def test_pipeline_date_precedence_filesystem_fallback(tmp_path: Path):
    """Verify that when no date is present in content, filesystem mtime is used."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "misc_notes.txt"
    test_file.write_text(
        "Random notes about the garden project without any date. The tomatoes "
        "are growing well this season and we should plan the fall cleanup "
        "before the first frost arrives next month.",
        encoding="utf-8",
    )

    executor = FilePipelineExecutor(target_root=target_dir)
    result = executor.process_file(test_file, dry_run=True)

    stat = test_file.stat()
    expected_mtime_date = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")

    assert result.details["date_source"] == "filesystem"
    assert result.details["date_value"] == expected_mtime_date
    assert result.proposed_relative_path.name.startswith(f"{expected_mtime_date}_")


def test_pipeline_date_precedence_exif_date(tmp_path: Path):
    """Verify that EXIF metadata date is identified as exif date_source."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "photo.jpg"
    test_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 20)

    # Use a mock understander that returns the exif date
    mock_und = GemmaUnderstander(
        mock=True,
        mock_response=UnderstandingResult(
            content_date="2023-08-25",
            file_description="family_photo",
            detected_entities=["Alpha"],
            category_hint="Photo",
            summary="Family photo",
        ),
    )
    executor = FilePipelineExecutor(target_root=target_dir, understander=mock_und)

    # Mock extractor to return exif_date matching understanding
    from unittest.mock import MagicMock
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = ExtractedContent(
        image_content=None,
        exif_date="2023-08-25",
        metadata_hints={"camera": "Canon"},
    )

    from unittest.mock import patch
    with patch("auto_file.core.executor.get_extractor_for_tool", return_value=mock_extractor):
        result = executor.process_file(test_file, dry_run=True)

    assert result.details["date_source"] == "exif"
    assert result.details["date_value"] == "2023-08-25"


# ==============================================================================
# Batch Directory Processing Tests
# ==============================================================================


def test_pipeline_batch_process_directory(tmp_path: Path):
    """Verify batch processing of directory with multiple files and audit run aggregation."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    (source_dir / "stmt.txt").write_text("Bank statement for Chase account 2026-01-15", encoding="utf-8")
    (source_dir / "med.txt").write_text("Alpha medical clinic pediatric report 2026-02-10", encoding="utf-8")
    (source_dir / "rcpt.txt").write_text("Receipt from Home Depot on 2026-03-01", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    results = executor.process_directory(source_dir, dry_run=False)
    assert len(results) == 3
    for res in results:
        assert res.status == "moved"
        assert res.destination_path.exists()

    # All files in inbox should have been moved out
    assert list(source_dir.iterdir()) == []

    # Check audit ledger
    history = ledger.get_history()
    assert len(history) == 1
    assert history[0]["mode"] == "cli_batch"
    assert history[0]["total_files"] == 3
    assert history[0]["successful_files"] == 3
    assert history[0]["failed_files"] == 0


def test_pipeline_batch_process_directory_dry_run(tmp_path: Path):
    """Verify batch processing in dry-run mode leaves all files intact."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    (source_dir / "doc1.txt").write_text("Alpha medical checkup 2026-01-01", encoding="utf-8")
    (source_dir / "doc2.txt").write_text("Chase bank statement 2026-02-01", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    results = executor.process_directory(source_dir, dry_run=True)
    assert len(results) == 2
    for res in results:
        assert res.status == "preview"
        assert res.original_path.exists()
        assert not res.destination_path.exists()

    # Audit ledger has no runs recorded for dry run
    assert len(ledger.get_history()) == 0


def test_pipeline_batch_process_directory_recursive(tmp_path: Path):
    """Verify recursive directory traversal discovers and moves nested files."""
    source_dir = tmp_path / "inbox"
    sub_dir = source_dir / "nested" / "sub"
    sub_dir.mkdir(parents=True)
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    (source_dir / "top.txt").write_text("Alpha medical note 2026-01-01", encoding="utf-8")
    (sub_dir / "nested_doc.txt").write_text("Chase bank statement 2026-02-01", encoding="utf-8")

    executor = FilePipelineExecutor(target_root=target_dir)

    # Non-recursive should find only top.txt
    res_non_rec = executor.process_directory(source_dir, dry_run=True, recursive=False)
    assert len(res_non_rec) == 1
    assert res_non_rec[0].original_path.name == "top.txt"

    # Recursive should find both
    res_rec = executor.process_directory(source_dir, dry_run=True, recursive=True)
    assert len(res_rec) == 2
    names = {r.original_path.name for r in res_rec}
    assert names == {"top.txt", "nested_doc.txt"}


# ==============================================================================
# Audit Ledger Rollback Verification
# ==============================================================================


def test_pipeline_audit_rollback_restores_files(tmp_path: Path):
    """Verify full end-to-end audit rollback restores moved files to their original location."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    f1 = source_dir / "file1.txt"
    f2 = source_dir / "file2.txt"
    f1.write_text("Medical record for Alpha on 2026-01-10", encoding="utf-8")
    f2.write_text("Chase bank statement on 2026-02-20", encoding="utf-8")

    f1_sha = compute_file_sha256(f1)
    f2_sha = compute_file_sha256(f2)

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    results = executor.process_directory(source_dir, dry_run=False)
    assert len(results) == 2
    assert not f1.exists()
    assert not f2.exists()

    # Now execute rollback of the batch run
    undone = ledger.rollback_run()
    assert len(undone) == 2

    # Original files should be restored and match original SHA-256
    assert f1.exists()
    assert f2.exists()
    assert compute_file_sha256(f1) == f1_sha
    assert compute_file_sha256(f2) == f2_sha

    # Destination files should no longer exist
    for res in results:
        assert not res.destination_path.exists()


# ==============================================================================
# Error Handling and Edge Cases
# ==============================================================================


def test_pipeline_error_handling_nonexistent_file(tmp_path: Path):
    """Verify handling of missing source files."""
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()
    missing_file = tmp_path / "does_not_exist.txt"

    executor = FilePipelineExecutor(target_root=target_dir)

    # By default, returns failed result
    res = executor.process_file(missing_file, raise_on_error=False)
    assert res.status == "failed"
    assert "not found" in (res.error_message or "").lower()

    # With raise_on_error=True, raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        executor.process_file(missing_file, raise_on_error=True)


def test_pipeline_error_handling_directory_as_file(tmp_path: Path):
    """Verify passing a directory to process_file returns failed or raises ValueError."""
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()
    sub_dir = tmp_path / "some_dir"
    sub_dir.mkdir()

    executor = FilePipelineExecutor(target_root=target_dir)
    res = executor.process_file(sub_dir, raise_on_error=False)
    assert res.status == "failed"
    assert "not a regular file" in (res.error_message or "").lower()


def test_pipeline_process_directory_missing_source(tmp_path: Path):
    """Verify process_directory raises FileNotFoundError for missing directory."""
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()
    executor = FilePipelineExecutor(target_root=target_dir)

    with pytest.raises(FileNotFoundError):
        executor.process_directory(tmp_path / "missing_dir")


def test_pipeline_result_dataclass_coercion():
    """Verify PipelineResult coerces string paths into Path instances."""
    res = PipelineResult(
        status="preview",
        original_path="/tmp/orig.txt",  # type: ignore[arg-type]
        destination_path="/tmp/dest.txt",  # type: ignore[arg-type]
        proposed_relative_path="dest.txt",  # type: ignore[arg-type]
    )
    assert isinstance(res.original_path, Path)
    assert isinstance(res.destination_path, Path)
    assert isinstance(res.proposed_relative_path, Path)


def test_pipeline_post_move_verification_failure_records_target_path(tmp_path: Path):
    """Verify that if move executes but verification fails, destination_path is recorded for rollback."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()
    audit_db = tmp_path / "audit.db"

    test_file = source_dir / "statement.txt"
    test_file.write_text("Chase bank statement for Alpha 2026-01-15", encoding="utf-8")
    real_sha = compute_file_sha256(test_file)

    ledger = AuditLedger(audit_db)
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    with patch(
        "auto_file.core.executor.compute_file_sha256",
        return_value="mismatched_sha256_hash_value",
    ):
        res = executor.process_file(test_file, raise_on_error=False)

    assert res.status == "failed"
    # Source was moved, so destination_path must point to target path where file actually is!
    assert not test_file.exists()
    assert res.destination_path.exists()
    assert res.destination_path != test_file
    assert "mismatch" in (res.error_message or "").lower()

    # Verify audit event recorded destination_path as resolved.target_path
    history = ledger.get_history()
    assert len(history) == 1
    events = ledger.get_events_for_run(history[0]["run_id"])
    assert len(events) == 1
    assert events[0]["status"] == "failed"
    assert events[0]["destination_path"] == str(res.destination_path)
    assert events[0]["original_path"] == str(test_file)


# ==============================================================================
# Understanding Gate Tests (needs_review)
# ==============================================================================


def test_pipeline_needs_review_leaves_unreadable_file_in_inbox(tmp_path: Path):
    """A file the understander cannot confidently read stays untouched."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "unknown_scan.txt"
    test_file.write_text("hi", encoding="utf-8")  # too little content to understand

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)

    result = executor.process_file(test_file, dry_run=False)
    assert result.status == "needs_review"
    assert test_file.exists()  # NOT moved, NOT renamed
    assert result.destination_path == test_file

    # The ledger records the needs_review event
    events = ledger.get_recent_events(limit=5)
    assert any(e["status"] == "needs_review" and e["original_path"] == str(test_file) for e in events)


def test_pipeline_dry_run_reports_needs_review(tmp_path: Path):
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "scan.txt"
    test_file.write_text("hi", encoding="utf-8")

    executor = FilePipelineExecutor(target_root=target_dir)
    result = executor.process_file(test_file, dry_run=True)
    assert result.status == "needs_review"
    assert test_file.exists()


def test_pipeline_needs_review_counts_as_handled_in_the_ledger(tmp_path: Path):
    """A file left for review was handled safely, not failed."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "unknown_scan.txt"
    test_file.write_text("hi", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)
    executor.process_directory(source_dir, dry_run=False)

    history = ledger.get_history()
    assert len(history) == 1
    assert history[0]["total_files"] == 1
    assert history[0]["successful_files"] == 1
    assert history[0]["failed_files"] == 0


def test_pipeline_moves_when_understanding_is_specific(tmp_path: Path):
    """Specific category from real content passes the gate."""
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()

    test_file = source_dir / "unknown_scan.txt"
    test_file.write_text(
        "Utility bill from City Power Company. Account 55201. "
        "Service address 12 Oak Street. Billing period September. "
        "Amount due $96.40, payment due by October 15th.",
        encoding="utf-8",
    )

    executor = FilePipelineExecutor(target_root=target_dir)
    result = executor.process_file(test_file, dry_run=False)
    assert result.status == "moved"
    assert not test_file.exists()


# ==============================================================================
# LLM Folder Routing Tests (Gemma picks from the real tree)
# ==============================================================================


class _RoutingStubUnderstander:
    """Stub with LLM routing: understands always, routes per configured status."""

    def __init__(self, status: str, folder: str | None = None):
        self._status = status
        self._folder = folder
        self.has_llm_routing = True
        self.last_choices: list[str] | None = None
        self.last_dynamic: list[str] | None = None

    def understand(self, content, filename_hint=None):
        return UnderstandingResult(
            content_date="2026-01-05",
            file_description="test_document",
            detected_entities=["Target"],
            category_hint="Receipt",
            summary="Receipt from Target for $23.45.",
            understood=True,
        )

    def route_with_llama(
        self,
        filename,
        summary,
        description,
        content_date,
        folder_choices,
        url=None,
        dynamic_folders=None,
    ):
        self.last_choices = list(folder_choices)
        self.last_dynamic = list(dynamic_folders or [])
        return self._status, self._folder


def _make_executor(tmp_path: Path, understander):
    ledger = AuditLedger(tmp_path / "audit.db")
    return FilePipelineExecutor(target_root=tmp_path / "sorted", audit_ledger=ledger, understander=understander)


def test_llm_routing_moves_to_chosen_folder(tmp_path: Path):
    src_dir = tmp_path / "inbox"; src_dir.mkdir()
    f = src_dir / "receipt.txt"
    f.write_text("Receipt from Target, purchase total $23.45, paid with card. Thank you for shopping with us today.", encoding="utf-8")

    stub = _RoutingStubUnderstander("ok", "Financial/Bills")
    executor = _make_executor(tmp_path, stub)
    result = executor.process_file(f, dry_run=False)

    assert result.status == "moved"
    assert result.destination_path.parent == tmp_path / "sorted" / "Financial" / "Bills"
    # The model saw the real folder tree
    assert "Financial/Bills" in stub.last_choices and "Misc" in stub.last_choices


def test_llm_routing_none_gates_to_needs_review(tmp_path: Path):
    src_dir = tmp_path / "inbox"; src_dir.mkdir()
    f = src_dir / "mystery.txt"
    f.write_text("Totally unclassifiable content." * 3, encoding="utf-8")

    stub = _RoutingStubUnderstander("none", None)
    executor = _make_executor(tmp_path, stub)
    result = executor.process_file(f, dry_run=False)

    assert result.status == "needs_review"
    assert f.exists()  # untouched


def test_llm_routing_invalid_folder_gates_to_needs_review(tmp_path: Path):
    src_dir = tmp_path / "inbox"; src_dir.mkdir()
    f = src_dir / "doc.txt"
    f.write_text("Receipt from Target, purchase total $23.45, paid with card. Thank you for shopping with us today.", encoding="utf-8")

    stub = _RoutingStubUnderstander("ok", "Financial/Bogus/MadeUp")
    executor = _make_executor(tmp_path, stub)
    result = executor.process_file(f, dry_run=False)

    assert result.status == "needs_review"
    assert f.exists()


def test_llm_routing_unreachable_falls_back_to_keyword_router(tmp_path: Path):
    src_dir = tmp_path / "inbox"; src_dir.mkdir()
    f = src_dir / "vehicle_registration.txt"
    f.write_text(
        "Vehicle registration document for Honda Civic, VIN 1HGCM82633A004352, "
        "registered owner Alpha Hardy, issued by the department of motor vehicles "
        "and valid through the end of next year, keep in the vehicle at all times.",
        encoding="utf-8",
    )

    stub = _RoutingStubUnderstander("unreachable", None)
    executor = _make_executor(tmp_path, stub)
    result = executor.process_file(f, dry_run=False)

    # No LLM reachable → the keyword router handles it (Property/Vehicles)
    assert result.status == "moved"
    assert str(result.proposed_relative_path).startswith("Financial/")
