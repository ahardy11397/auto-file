"""Tests for the Auto-File CLI interface."""

from pathlib import Path
import pytest
from typer.testing import CliRunner

from auto_file.cli import app
from auto_file.storage.audit import AuditLedger

runner = CliRunner()


def test_cli_help():
    """Verify CLI help displays top-level commands and description."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "sort" in result.output
    assert "history" in result.output
    assert "undo" in result.output
    assert "config" in result.output
    assert "Auto-File System" in result.output


def test_cli_dry_run_sort(tmp_path: Path):
    """Verify sort --dry-run previews destination in rich table and leaves file untouched."""
    f = tmp_path / "doc.txt"
    f.write_text("Medical record for Alpha", encoding="utf-8")
    dest_dir = tmp_path / "sorted"
    audit_db = tmp_path / "audit.db"

    result = runner.invoke(
        app,
        ["sort", str(f), "--dry-run", "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert result.exit_code == 0
    assert f.exists()
    assert not (dest_dir / "doc.txt").exists()
    # Check table headers in output
    assert "Source File" in result.output
    assert "Tool" in result.output
    assert "Date" in result.output
    assert "Proposed Destination" in result.output
    assert "Status" in result.output
    assert "preview" in result.output


def test_cli_live_sort_single_file(tmp_path: Path):
    """Verify live sort moves file and records audit ledger entry."""
    f = tmp_path / "statement.txt"
    f.write_text("Bank statement for Chase checking account 2026-05-12", encoding="utf-8")
    dest_dir = tmp_path / "sorted"
    audit_db = tmp_path / "audit.db"

    result = runner.invoke(
        app,
        ["sort", str(f), "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert result.exit_code == 0
    assert not f.exists()
    assert "moved" in result.output

    # Check ledger
    ledger = AuditLedger(audit_db)
    history = ledger.get_history()
    assert len(history) == 1
    events = ledger.get_events_for_run(history[0]["run_id"])
    assert len(events) == 1
    assert events[0]["status"] == "moved"
    assert Path(events[0]["destination_path"]).exists()


def test_cli_sort_directory(tmp_path: Path):
    """Verify sort processes all files in a directory."""
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "file1.txt").write_text("Receipt from Target", encoding="utf-8")
    (inbox / "file2.txt").write_text("Blood test results for Echo", encoding="utf-8")

    dest_dir = tmp_path / "sorted"
    audit_db = tmp_path / "audit.db"

    result = runner.invoke(
        app,
        ["sort", str(inbox), "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert result.exit_code == 0
    assert not (inbox / "file1.txt").exists()
    assert not (inbox / "file2.txt").exists()
    assert "file1.txt" in result.output
    assert "file2.txt" in result.output


def test_cli_sort_recursive_directory(tmp_path: Path):
    """Verify sort --recursive processes files in nested subdirectories."""
    inbox = tmp_path / "inbox"
    sub = inbox / "subfolder"
    sub.mkdir(parents=True)
    (sub / "nested.txt").write_text("Court document legal notice", encoding="utf-8")

    dest_dir = tmp_path / "sorted"
    audit_db = tmp_path / "audit.db"

    # Non-recursive should ignore nested
    result_non_rec = runner.invoke(
        app,
        ["sort", str(inbox), "--dry-run", "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert result_non_rec.exit_code == 0
    assert "nested.txt" not in result_non_rec.output

    # Recursive should find it
    result_rec = runner.invoke(
        app,
        ["sort", str(inbox), "--recursive", "--dry-run", "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert result_rec.exit_code == 0
    assert "nested.txt" in result_rec.output


def test_cli_sort_missing_file_errors(tmp_path: Path):
    """Verify sort exits with error when path does not exist."""
    missing = tmp_path / "nonexistent.txt"
    dest_dir = tmp_path / "sorted"

    result = runner.invoke(app, ["sort", str(missing), "--dest", str(dest_dir)])
    assert result.exit_code != 0
    assert "does not exist" in result.output or "not found" in result.output.lower()


def test_cli_sort_missing_dest_errors(tmp_path: Path):
    """Verify sort exits with error when destination is not specified and not configured."""
    f = tmp_path / "doc.txt"
    f.write_text("Hello world", encoding="utf-8")
    cfg_file = tmp_path / "empty_config.json"
    cfg_file.write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["sort", str(f), "--config-file", str(cfg_file)])
    assert result.exit_code != 0
    assert "destination" in result.output.lower()


def test_cli_history_empty_and_populated(tmp_path: Path):
    """Verify history displays rich table of runs."""
    audit_db = tmp_path / "audit.db"
    dest_dir = tmp_path / "sorted"
    f = tmp_path / "receipt.txt"
    f.write_text("Receipt from grocery store", encoding="utf-8")

    # History before any runs
    res_empty = runner.invoke(app, ["history", "--audit-db", str(audit_db)])
    assert res_empty.exit_code == 0
    assert "No run history" in res_empty.output or "Run ID" in res_empty.output

    # Perform a run
    sort_res = runner.invoke(
        app,
        ["sort", str(f), "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert sort_res.exit_code == 0

    # History after run
    res_history = runner.invoke(app, ["history", "--audit-db", str(audit_db)])
    assert res_history.exit_code == 0
    assert "Run ID" in res_history.output
    assert "Mode" in res_history.output
    assert "cli_single" in res_history.output

    # Test limit option
    res_limit = runner.invoke(app, ["history", "--limit", "1", "--audit-db", str(audit_db)])
    assert res_limit.exit_code == 0


def test_cli_undo_last_run(tmp_path: Path):
    """Verify undo --last restores moved files to their original location."""
    audit_db = tmp_path / "audit.db"
    dest_dir = tmp_path / "sorted"
    f = tmp_path / "vehicle_registration.txt"
    f.write_text("Vehicle registration document for Honda Civic", encoding="utf-8")

    # Live sort
    sort_res = runner.invoke(
        app,
        ["sort", str(f), "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert sort_res.exit_code == 0
    assert not f.exists()

    # Undo
    undo_res = runner.invoke(app, ["undo", "--last", "--audit-db", str(audit_db)])
    assert undo_res.exit_code == 0
    assert f.exists()
    assert "rolled_back" in undo_res.output or "Restored" in undo_res.output


def test_cli_undo_by_run_id(tmp_path: Path):
    """Verify undo --run-id restores specific run."""
    audit_db = tmp_path / "audit.db"
    dest_dir = tmp_path / "sorted"
    f = tmp_path / "court_record.txt"
    f.write_text("Court legal notice", encoding="utf-8")

    sort_res = runner.invoke(
        app,
        ["sort", str(f), "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert sort_res.exit_code == 0
    assert not f.exists()

    ledger = AuditLedger(audit_db)
    run_id = ledger.get_history()[0]["run_id"]

    undo_res = runner.invoke(
        app,
        ["undo", "--run-id", run_id, "--audit-db", str(audit_db)],
    )
    assert undo_res.exit_code == 0
    assert f.exists()


def test_cli_config_commands(tmp_path: Path):
    """Verify config get, set, and show operations."""
    cfg_file = tmp_path / "config.json"

    # Set destination
    res_set = runner.invoke(
        app,
        ["config", "--set", "dest", "/default/dest", "--config-file", str(cfg_file)],
    )
    assert res_set.exit_code == 0
    assert "/default/dest" in res_set.output

    # Get destination
    res_get = runner.invoke(
        app,
        ["config", "--get", "dest", "--config-file", str(cfg_file)],
    )
    assert res_get.exit_code == 0
    assert "/default/dest" in res_get.output

    # Show all
    res_show = runner.invoke(
        app,
        ["config", "--show", "--config-file", str(cfg_file)],
    )
    assert res_show.exit_code == 0
    assert "dest" in res_show.output
    assert "/default/dest" in res_show.output

    # Fallback syntax: config set key val / config get key
    res_sub_set = runner.invoke(
        app,
        ["config", "set", "source", "/default/inbox", "--config-file", str(cfg_file)],
    )
    assert res_sub_set.exit_code == 0

    res_sub_get = runner.invoke(
        app,
        ["config", "get", "source", "--config-file", str(cfg_file)],
    )
    assert res_sub_get.exit_code == 0
    assert "/default/inbox" in res_sub_get.output


def test_cli_version():
    """Verify --version option outputs package version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "auto-file v" in result.output


def test_cli_no_args():
    """Verify invoking with no arguments shows help."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage: " in result.output
    assert "sort" in result.output


def test_cli_sort_uses_configured_dest(tmp_path: Path):
    """Verify sort uses default destination configured in config file when --dest is omitted."""
    cfg_file = tmp_path / "config.json"
    dest_dir = tmp_path / "sorted_via_cfg"
    runner.invoke(app, ["config", "--set", "dest", str(dest_dir), "--config-file", str(cfg_file)])

    f = tmp_path / "bill.txt"
    f.write_text("Electric utility bill from PG&E 2026-03-01", encoding="utf-8")
    audit_db = tmp_path / "audit.db"

    result = runner.invoke(
        app,
        ["sort", str(f), "--config-file", str(cfg_file), "--audit-db", str(audit_db)],
    )
    assert result.exit_code == 0
    assert not f.exists()
    assert dest_dir.exists()


def test_cli_undo_no_files_to_undo(tmp_path: Path):
    """Verify undo message when no moved files exist in audit ledger."""
    audit_db = tmp_path / "audit.db"
    # Create empty audit ledger
    AuditLedger(audit_db)

    result = runner.invoke(app, ["undo", "--last", "--audit-db", str(audit_db)])
    assert result.exit_code == 0
    assert "No moved files" in result.output


def test_cli_undo_nonexistent_audit_db(tmp_path: Path):
    """Verify undo handles nonexistent audit db gracefully."""
    missing_db = tmp_path / "nonexistent_audit.db"

    result = runner.invoke(app, ["undo", "--last", "--audit-db", str(missing_db)])
    assert result.exit_code != 0
    assert "does not exist" in result.output


def test_cli_history_with_run_id(tmp_path: Path):
    """Verify history --run-id shows file events for a specific run."""
    audit_db = tmp_path / "audit.db"
    dest_dir = tmp_path / "sorted"
    f = tmp_path / "lease.txt"
    f.write_text("Apartment rental lease agreement", encoding="utf-8")

    sort_res = runner.invoke(
        app,
        ["sort", str(f), "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert sort_res.exit_code == 0

    ledger = AuditLedger(audit_db)
    run_id = ledger.get_history()[0]["run_id"]

    hist_res = runner.invoke(app, ["history", "--run-id", run_id, "--audit-db", str(audit_db)])
    assert hist_res.exit_code == 0
    assert "File Events for Run" in hist_res.output
    assert "lease.txt" in hist_res.output
    assert "moved" in hist_res.output

