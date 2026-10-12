"""Tests for SQLite audit ledger and rollback engine."""

import hashlib
from pathlib import Path
import pytest

from auto_file.storage.audit import (
    AuditLedger,
    AuditError,
    RollbackError,
    RollbackVerificationError,
    RollbackMissingFileError,
)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def test_audit_lifecycle_and_rollback(tmp_path: Path):
    """Basic lifecycle test from task specification."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)
    run_id = ledger.start_run(mode="cli_single", source_root="/inbox", target_root="/sorted")

    src = tmp_path / "source.txt"
    src.write_text("data")
    dest = tmp_path / "sorted" / "2026-01-01_source.txt"
    dest.parent.mkdir()
    dest.write_text("data")

    event_id = ledger.record_event(
        run_id=run_id,
        original_path=str(src),
        destination_path=str(dest),
        sha256="hash123",
        file_size=4,
        date_source="content",
        date_value="2026-01-01",
        description="source",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="moved",
    )
    assert event_id is not None

    # Test undo
    events_undone = ledger.rollback_run(run_id)
    assert len(events_undone) == 1
    assert src.exists()
    assert not dest.exists()


def test_finish_run_and_get_history(tmp_path: Path):
    """Test start_run, finish_run, and get_history pagination."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)

    run1 = ledger.start_run(mode="cli_single", source_root="/inbox1", target_root="/out1")
    ledger.finish_run(run1, total_files=5, successful_files=4, failed_files=1)

    run2 = ledger.start_run(mode="watch_daemon", source_root="/inbox2", target_root="/out2")
    ledger.finish_run(run2, total_files=10, successful_files=10, failed_files=0)

    history = ledger.get_history(limit=10)
    assert len(history) == 2
    # Most recent run first
    assert history[0]["run_id"] == run2
    assert history[0]["mode"] == "watch_daemon"
    assert history[0]["total_files"] == 10
    assert history[0]["completed_at"] is not None

    assert history[1]["run_id"] == run1
    assert history[1]["mode"] == "cli_single"
    assert history[1]["total_files"] == 5

    # Test history limit
    limited = ledger.get_history(limit=1)
    assert len(limited) == 1
    assert limited[0]["run_id"] == run2


def test_finish_run_auto_aggregates_counts(tmp_path: Path):
    """Test finish_run auto-counts from file_events when 0 is passed."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)

    run_id = ledger.start_run(mode="cli_batch", source_root="/in", target_root="/out")
    ledger.record_event(
        run_id=run_id,
        original_path="/in/1.txt",
        destination_path="/out/1.txt",
        sha256="hash1",
        file_size=10,
        date_source="content",
        date_value="2026-01-01",
        description="one",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="moved",
    )
    ledger.record_event(
        run_id=run_id,
        original_path="/in/2.txt",
        destination_path="/out/2.txt",
        sha256="hash2",
        file_size=20,
        date_source="content",
        date_value="2026-01-01",
        description="two",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="duplicate_skipped",
    )
    ledger.record_event(
        run_id=run_id,
        original_path="/in/3.txt",
        destination_path="/out/3.txt",
        sha256="hash3",
        file_size=30,
        date_source="content",
        date_value="2026-01-01",
        description="three",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="failed",
        error_message="disk full",
    )

    ledger.finish_run(run_id)
    run_record = ledger.get_run(run_id)
    assert run_record is not None
    assert run_record["total_files"] == 3
    assert run_record["successful_files"] == 2
    assert run_record["failed_files"] == 1


def test_rollback_reverse_order(tmp_path: Path):
    """Test that events are rolled back in reverse chronological order."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)
    run_id = ledger.start_run(mode="cli_single", source_root="/inbox", target_root="/sorted")

    events = []
    dest_dir = tmp_path / "sorted"
    dest_dir.mkdir()

    for i in range(3):
        src = tmp_path / f"file_{i}.txt"
        dest = dest_dir / f"2026-01-01_file_{i}.txt"
        content = f"content_{i}".encode("utf-8")
        dest.write_bytes(content)

        eid = ledger.record_event(
            run_id=run_id,
            original_path=str(src),
            destination_path=str(dest),
            sha256=_sha256(content),
            file_size=len(content),
            date_source="content",
            date_value="2026-01-01",
            description=f"file_{i}",
            laya_tool_selected="text_extractor",
            laya_category_selected="Misc",
            status="moved",
            timestamp=f"2026-01-01T00:00:0{i}Z",
        )
        events.append(eid)

    undone = ledger.rollback_run(run_id)
    assert len(undone) == 3
    # Reverse order: file 2, file 1, file 0
    assert undone[0]["description"] == "file_2"
    assert undone[1]["description"] == "file_1"
    assert undone[2]["description"] == "file_0"

    for i in range(3):
        assert (tmp_path / f"file_{i}.txt").exists()
        assert not (dest_dir / f"2026-01-01_file_{i}.txt").exists()


def test_rollback_latest_run_when_run_id_none(tmp_path: Path):
    """When run_id is None, rollback rolls back the latest run with moved files."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)

    run1 = ledger.start_run(mode="cli_single", source_root="/inbox", target_root="/sorted")
    src1 = tmp_path / "f1.txt"
    dest1 = tmp_path / "sorted" / "f1.txt"
    dest1.parent.mkdir(parents=True, exist_ok=True)
    c1 = b"c1"
    dest1.write_bytes(c1)
    ledger.record_event(
        run_id=run1,
        original_path=str(src1),
        destination_path=str(dest1),
        sha256=_sha256(c1),
        file_size=len(c1),
        date_source="content",
        date_value="2026-01-01",
        description="f1",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="moved",
    )

    run2 = ledger.start_run(mode="cli_single", source_root="/inbox", target_root="/sorted")
    src2 = tmp_path / "f2.txt"
    dest2 = tmp_path / "sorted" / "f2.txt"
    c2 = b"c2"
    dest2.write_bytes(c2)
    ledger.record_event(
        run_id=run2,
        original_path=str(src2),
        destination_path=str(dest2),
        sha256=_sha256(c2),
        file_size=len(c2),
        date_source="content",
        date_value="2026-01-01",
        description="f2",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="moved",
    )

    # Rollback latest run (should be run2)
    undone = ledger.rollback_run()
    assert len(undone) == 1
    assert undone[0]["run_id"] == run2
    assert src2.exists()
    assert not dest2.exists()
    # run1 should still be untouched
    assert dest1.exists()
    assert not src1.exists()


def test_rollback_hash_mismatch_raises_strict(tmp_path: Path):
    """Rollback fails with RollbackVerificationError if target file was modified."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)
    run_id = ledger.start_run(mode="cli_single", source_root="/inbox", target_root="/sorted")

    src = tmp_path / "important.doc"
    dest = tmp_path / "sorted" / "2026-01-01_important.doc"
    dest.parent.mkdir(parents=True, exist_ok=True)
    orig_content = b"original safe content"
    dest.write_bytes(b"tampered modified content")

    recorded_hash = _sha256(orig_content)
    ledger.record_event(
        run_id=run_id,
        original_path=str(src),
        destination_path=str(dest),
        sha256=recorded_hash,
        file_size=len(orig_content),
        date_source="content",
        date_value="2026-01-01",
        description="important",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="moved",
    )

    with pytest.raises(RollbackVerificationError) as exc_info:
        ledger.rollback_run(run_id, strict=True)

    assert "SHA-256 verification failed" in str(exc_info.value)
    # File must NOT have been moved or destroyed
    assert dest.exists()
    assert not src.exists()

    # Database status should remain 'moved'
    events = ledger.get_events_for_run(run_id)
    assert events[0]["status"] == "moved"


def test_rollback_hash_mismatch_skips_when_not_strict(tmp_path: Path):
    """Rollback skips modified files when strict=False without raising."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)
    run_id = ledger.start_run(mode="cli_single", source_root="/inbox", target_root="/sorted")

    src = tmp_path / "doc.txt"
    dest = tmp_path / "sorted" / "doc.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(b"altered content")

    ledger.record_event(
        run_id=run_id,
        original_path=str(src),
        destination_path=str(dest),
        sha256=_sha256(b"original content"),
        file_size=16,
        date_source="content",
        date_value="2026-01-01",
        description="doc",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="moved",
    )

    undone = ledger.rollback_run(run_id, strict=False)
    assert len(undone) == 1
    assert undone[0]["status"] == "skipped"
    assert "SHA-256 verification failed" in undone[0]["error_message"]
    assert dest.exists()


def test_rollback_missing_destination_file(tmp_path: Path):
    """Rollback handles missing destination files appropriately."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)
    run_id = ledger.start_run(mode="cli_single", source_root="/inbox", target_root="/sorted")

    src = tmp_path / "vanished.txt"
    dest = tmp_path / "sorted" / "vanished.txt"
    # Destination intentionally does not exist

    ledger.record_event(
        run_id=run_id,
        original_path=str(src),
        destination_path=str(dest),
        sha256=_sha256(b"content"),
        file_size=7,
        date_source="content",
        date_value="2026-01-01",
        description="vanished",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="moved",
    )

    # In strict mode: raises RollbackMissingFileError
    with pytest.raises(RollbackMissingFileError):
        ledger.rollback_run(run_id, strict=True)

    # In non-strict mode: flags as skipped
    undone = ledger.rollback_run(run_id, strict=False)
    assert len(undone) == 1
    assert undone[0]["status"] == "skipped"
    assert "does not exist" in undone[0]["error_message"]


def test_rollback_recreates_parent_directories(tmp_path: Path):
    """Rollback creates original parent directories if they no longer exist."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)
    run_id = ledger.start_run(mode="cli_single", source_root="/inbox", target_root="/sorted")

    deep_orig = tmp_path / "nested" / "inbox" / "folder" / "document.txt"
    dest = tmp_path / "sorted" / "document.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = b"nested document payload"
    dest.write_bytes(content)

    assert not deep_orig.parent.exists()

    ledger.record_event(
        run_id=run_id,
        original_path=str(deep_orig),
        destination_path=str(dest),
        sha256=_sha256(content),
        file_size=len(content),
        date_source="content",
        date_value="2026-01-01",
        description="document",
        laya_tool_selected="text_extractor",
        laya_category_selected="Misc",
        status="moved",
    )

    undone = ledger.rollback_run(run_id)
    assert len(undone) == 1
    assert deep_orig.exists()
    assert deep_orig.read_bytes() == content
    assert not dest.exists()


def test_empty_database_rollback(tmp_path: Path):
    """Rollback on an empty database returns empty list."""
    db_path = tmp_path / "audit.db"
    ledger = AuditLedger(db_path)
    assert ledger.rollback_run() == []
    assert ledger.get_history() == []


def test_context_manager_support(tmp_path: Path):
    """Test using AuditLedger as a context manager."""
    db_path = tmp_path / "audit.db"
    with AuditLedger(db_path) as ledger:
        run_id = ledger.start_run(mode="cli_single", source_root="/a", target_root="/b")
        assert run_id is not None
