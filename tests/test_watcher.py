"""Tests for the background folder watcher daemon."""

from __future__ import annotations

from pathlib import Path
import time
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from auto_file.cli import app
from auto_file.core.executor import FilePipelineExecutor, PipelineResult
from auto_file.core.watcher import FolderWatcher
from auto_file.storage.audit import AuditLedger

runner = CliRunner()


def test_watcher_detects_and_sorts_file(tmp_path: Path):
    """Verify watcher detects a newly written file, debounces, and moves it to sorted dir."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.5)

    watcher.start()
    try:
        f = inbox / "test_doc.txt"
        f.write_text("Alpha dental medical appointment note", encoding="utf-8")
        time.sleep(1.5)
        # File should have been processed and moved out of inbox
        assert not f.exists()

        # Verify sorted file was created in destination
        sorted_files = list(sorted_dir.rglob("*.txt"))
        assert len(sorted_files) == 1
        assert "Alpha" in sorted_files[0].read_text(encoding="utf-8")
    finally:
        watcher.stop()


def test_watcher_ignores_hidden_files(tmp_path: Path):
    """Verify hidden files (starting with dot) are ignored by the watcher."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.3)

    watcher.start()
    try:
        hidden_file = inbox / ".hidden_note.txt"
        hidden_file.write_text("Secret note not to be organized", encoding="utf-8")
        time.sleep(0.8)

        # Hidden file should remain in inbox
        assert hidden_file.exists()
        assert len(list(sorted_dir.rglob("*"))) == 0
    finally:
        watcher.stop()


def test_watcher_ignores_temporary_extensions(tmp_path: Path):
    """Verify temporary download extensions (.tmp, .part, .crdownload) are ignored."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.3)

    watcher.start()
    try:
        f_tmp = inbox / "download.tmp"
        f_part = inbox / "download.part"
        f_cr = inbox / "download.crdownload"

        f_tmp.write_text("Temporary file chunk", encoding="utf-8")
        f_part.write_text("Partial download chunk", encoding="utf-8")
        f_cr.write_text("Chrome download chunk", encoding="utf-8")

        time.sleep(0.8)

        assert f_tmp.exists()
        assert f_part.exists()
        assert f_cr.exists()
        assert len(list(sorted_dir.rglob("*"))) == 0
    finally:
        watcher.stop()


def test_watcher_processes_renamed_temp_file(tmp_path: Path):
    """Verify that when a temp download is renamed to a completed file, it is processed."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.4)

    watcher.start()
    try:
        downloading = inbox / "statement.crdownload"
        downloading.write_text("Chase bank statement checking 2026-04-10", encoding="utf-8")
        time.sleep(0.2)
        assert downloading.exists()

        completed = inbox / "statement.txt"
        downloading.rename(completed)

        time.sleep(1.2)
        assert not completed.exists()
        assert not downloading.exists()

        sorted_files = list(sorted_dir.rglob("*.txt"))
        assert len(sorted_files) == 1
    finally:
        watcher.stop()


def test_watcher_debounce_waits_for_file_stability(tmp_path: Path):
    """Verify that debounce resets when file continues to be appended to."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    # Debounce of 0.6 seconds
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.6)

    watcher.start()
    try:
        f = inbox / "growing_log.txt"
        f.write_text("Initial log entry\n", encoding="utf-8")

        # Sleep less than debounce and append again
        time.sleep(0.3)
        with open(f, "a", encoding="utf-8") as fp:
            fp.write("Second log entry\n")

        # Check it is still in inbox because timer was reset
        time.sleep(0.3)
        assert f.exists()

        with open(f, "a", encoding="utf-8") as fp:
            fp.write("Chase bank statement closing summary for the checking account, ending balance and transaction count included for the period.\n")

        # Now wait for stability (debounce window + margin)
        time.sleep(1.2)
        assert not f.exists()

        sorted_files = list(sorted_dir.rglob("*.txt"))
        assert len(sorted_files) == 1
    finally:
        watcher.stop()


def test_watcher_recursive_mode(tmp_path: Path):
    """Verify recursive=True processes files in subdirectories."""
    inbox = tmp_path / "inbox"
    sub = inbox / "nested"
    sub.mkdir(parents=True)
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.4, recursive=True)

    watcher.start()
    try:
        nested_file = sub / "nested_doc.txt"
        nested_file.write_text("Target receipt grocery store purchase", encoding="utf-8")
        time.sleep(1.2)

        assert not nested_file.exists()
        sorted_files = list(sorted_dir.rglob("*.txt"))
        assert len(sorted_files) == 1
    finally:
        watcher.stop()


def test_watcher_non_recursive_mode_ignores_subdirectories(tmp_path: Path):
    """Verify recursive=False ignores files created in subdirectories."""
    inbox = tmp_path / "inbox"
    sub = inbox / "nested"
    sub.mkdir(parents=True)
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.4, recursive=False)

    watcher.start()
    try:
        nested_file = sub / "nested_doc.txt"
        nested_file.write_text("Target receipt grocery store purchase", encoding="utf-8")
        time.sleep(0.8)

        # File in subfolder should NOT be moved when recursive=False
        assert nested_file.exists()
    finally:
        watcher.stop()


def test_watcher_sorts_files_already_in_inbox_at_startup(tmp_path: Path):
    """Files present before start() (e.g. dropped while the service was down)
    must be sorted by the startup scan, not sit forever until a new event."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    existing = inbox / "pre_existing.txt"
    existing.write_text("Alpha dental medical appointment note from the clinic, cleaning and checkup completed, next visit scheduled in six months.", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.5)

    watcher.start()
    try:
        time.sleep(1.5)
        assert not existing.exists()
        sorted_files = list(sorted_dir.rglob("*.txt"))
        assert len(sorted_files) == 1
    finally:
        watcher.stop()


def test_watcher_ignores_do_not_move_placeholder(tmp_path: Path):
    """The do-not-move-or-delete-this-file placeholder must stay in the inbox,
    even when present at startup (startup scan) or freshly created."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    placeholder = inbox / "do-not-move-or-delete-this-file"
    placeholder.write_text("", encoding="utf-8")

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.4)

    watcher.start()
    try:
        # Rewrite it after start so the created/modified event path is covered too
        placeholder.write_text("", encoding="utf-8")
        time.sleep(1.2)
        assert placeholder.exists()
        assert not placeholder.name in {p.name for p in sorted_dir.rglob("*")}
    finally:
        watcher.stop()


def test_watcher_context_manager(tmp_path: Path):
    """Verify FolderWatcher context manager starts and stops cleanly."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)

    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.5)
    assert not watcher.is_running

    with watcher:
        assert watcher.is_running

    assert not watcher.is_running


def test_watcher_on_processed_callback(tmp_path: Path):
    """Verify on_processed callback receives PipelineResult."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    sorted_dir = tmp_path / "sorted"
    sorted_dir.mkdir()

    processed_results: list[PipelineResult] = []

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(
        inbox_dir=inbox,
        executor=executor,
        debounce_seconds=0.4,
        on_processed=processed_results.append,
    )

    with watcher:
        f = inbox / "callback_doc.txt"
        f.write_text("Alpha medical and dental appointment notes from the clinic, cleaning and checkup completed, next visit scheduled in six months.", encoding="utf-8")
        time.sleep(1.2)

        assert not f.exists()
        assert len(processed_results) == 1
        assert processed_results[0].status == "moved"


def test_cli_watch_invalid_inbox():
    """Verify CLI watch errors when inbox directory does not exist."""
    result = runner.invoke(app, ["watch", "/nonexistent/inbox/dir", "--dest", "/tmp/dest"])
    assert result.exit_code == 1
    assert "Inbox directory does not exist" in result.output


def test_cli_watch_inbox_not_a_directory(tmp_path: Path):
    """Verify CLI watch errors when inbox path is a regular file."""
    f = tmp_path / "not_a_dir.txt"
    f.write_text("hello", encoding="utf-8")
    result = runner.invoke(app, ["watch", str(f), "--dest", str(tmp_path / "dest")])
    assert result.exit_code == 1
    assert "Inbox path is not a directory" in result.output


def test_cli_watch_missing_dest(tmp_path: Path):
    """Verify CLI watch errors when destination is not specified and no default configured."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    empty_config = tmp_path / "empty_config.json"
    empty_config.write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        ["watch", str(inbox), "--config-file", str(empty_config)],
    )
    assert result.exit_code == 1
    assert "Destination directory not specified" in result.output


def test_cli_watch_clean_interrupt(tmp_path: Path):
    """Verify CLI watch starts FolderWatcher and stops cleanly upon KeyboardInterrupt."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    dest = tmp_path / "dest"
    dest.mkdir()
    audit_db = tmp_path / "audit.db"

    # Patch time.sleep in the watch loop to simulate KeyboardInterrupt
    with patch("time.sleep", side_effect=KeyboardInterrupt):
        result = runner.invoke(
            app,
            ["watch", str(inbox), "--dest", str(dest), "--audit-db", str(audit_db)],
        )

    assert result.exit_code == 0
    assert "Watching directory" in result.output
    assert "Stopping watcher daemon" in result.output
    assert "Watcher stopped cleanly" in result.output


def test_watcher_processes_files_when_inbox_inside_target_root(tmp_path: Path):
    """Regression: with inbox nested inside the destination root (e.g.
    Cabinet/Inbox with dest=Cabinet), inbox files must still be processed
    while already-sorted areas of the destination stay untouched."""
    dest = tmp_path / "cabinet"
    dest.mkdir()
    inbox = dest / "Inbox"
    inbox.mkdir()
    # An already-sorted area of the destination, outside the inbox
    (dest / "Financial").mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=dest, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.3)

    # Already-sorted areas are ignored...
    assert watcher.is_ignored(dest / "Financial" / "sorted.txt")
    # ...but incoming inbox files are not
    assert not watcher.is_ignored(inbox / "new_file.txt")

    watcher.start()
    try:
        incoming = inbox / "storage receipt.txt"
        incoming.write_text("storage unit rental receipt paid in full", encoding="utf-8")
        time.sleep(1.2)
        assert not incoming.exists()
        assert any("receipt" in p.name.lower() for p in dest.rglob("*.txt") if "Inbox" not in p.parts)
    finally:
        watcher.stop()


def test_watcher_boundary_checks_and_nested_target_root(tmp_path: Path):
    """Verify watcher ignores files outside inbox and ignores files inside nested target_root."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    # Nested target_root inside inbox
    sorted_dir = inbox / "sorted"
    sorted_dir.mkdir()

    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=sorted_dir, audit_ledger=ledger)
    watcher = FolderWatcher(inbox_dir=inbox, executor=executor, debounce_seconds=0.3, recursive=True)

    # 1. Test boundary rejection of paths outside inbox
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("Outside file", encoding="utf-8")
    watcher._queue_file(outside_file)
    assert outside_file.resolve() not in watcher._pending

    # 2. Test loop prevention: files created directly in nested target_root are ignored
    inside_target_file = sorted_dir / "already_sorted.txt"
    inside_target_file.write_text("Already sorted document", encoding="utf-8")
    watcher._queue_file(inside_target_file)
    assert inside_target_file.resolve() not in watcher._pending
    assert watcher.is_ignored(inside_target_file)

    # 3. Live watcher verification: incoming files in inbox are organized into nested sorted_dir
    # without causing an infinite recursive re-sorting loop
    watcher.start()
    try:
        incoming = inbox / "medical_report.txt"
        incoming.write_text("Alpha medical appointment doctor dental checkup", encoding="utf-8")
        time.sleep(1.2)

        # Incoming file should be moved
        assert not incoming.exists()
        # Pre-existing file inside nested target_root should remain untouched
        assert inside_target_file.exists()
        # Destination folder should contain the organized file
        sorted_files = list(sorted_dir.rglob("*.txt"))
        assert len(sorted_files) >= 2
    finally:
        watcher.stop()
