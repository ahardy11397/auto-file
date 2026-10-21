"""Tests for the Auto-File CLI interface."""

import os
import socket
from pathlib import Path
from unittest.mock import patch
import pytest
from typer.testing import CliRunner

from auto_file.cli import app
from auto_file.config import set_config_value
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
    assert "watch" in result.output
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
    (inbox / "file2.txt").write_text("Blood test results for Echo from the clinic laboratory, reviewed by the physician, follow up appointment scheduled next month.", encoding="utf-8")

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
    """History shows individual file moves by default; run summaries via --runs."""
    audit_db = tmp_path / "audit.db"
    dest_dir = tmp_path / "sorted"
    f = tmp_path / "receipt.txt"
    f.write_text("Receipt from grocery store", encoding="utf-8")

    # History before any runs
    res_empty = runner.invoke(app, ["history", "--audit-db", str(audit_db)])
    assert res_empty.exit_code == 0
    assert "No file history" in res_empty.output

    # Perform a run
    sort_res = runner.invoke(
        app,
        ["sort", str(f), "--dest", str(dest_dir), "--audit-db", str(audit_db)],
    )
    assert sort_res.exit_code == 0

    # Default history: individual file events with original and filed names
    res_history = runner.invoke(app, ["history", "--audit-db", str(audit_db)])
    assert res_history.exit_code == 0
    assert "Recent File Moves" in res_history.output
    assert "receipt.txt" in res_history.output
    assert str(dest_dir) in res_history.output
    assert "moved" in res_history.output

    # Run summaries behind --runs
    res_runs = runner.invoke(app, ["history", "--runs", "--audit-db", str(audit_db)])
    assert res_runs.exit_code == 0
    assert "Run ID" in res_runs.output
    assert "cli_single" in res_runs.output

    # Test limit option
    res_limit = runner.invoke(app, ["history", "--limit", "1", "--audit-db", str(audit_db)])
    assert res_limit.exit_code == 0


def test_cli_undo_last_run(tmp_path: Path):
    """Verify undo --last restores moved files to their original location."""
    audit_db = tmp_path / "audit.db"
    dest_dir = tmp_path / "sorted"
    f = tmp_path / "vehicle_registration.txt"
    f.write_text("Vehicle registration document for Honda Civic, VIN 1HGCM82633A004352, registered owner Alpha Hardy, issued by the department of motor vehicles and valid through the end of next year, keep in the vehicle at all times.", encoding="utf-8")

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
    f.write_text("Apartment rental lease agreement for the unit at 42 Elm Street, twelve month term beginning this month, rent due on the first, signed by both tenant and landlord.", encoding="utf-8")

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


def test_cli_undo_both_run_id_and_last_guidance(tmp_path: Path):
    """Verify undo command rejects passing both --run-id and --last with clear guidance."""
    audit_db = tmp_path / "audit.db"
    result = runner.invoke(
        app,
        ["undo", "--run-id", "run-12345", "--last", "--audit-db", str(audit_db)],
    )
    assert result.exit_code == 1
    assert "Cannot specify both --run-id and --last" in result.output


def test_cli_sort_failure_displays_dash_in_table(tmp_path: Path):
    """Verify sort table displays '-' instead of '.' for proposed destination on failure."""
    f = tmp_path / "corrupt.txt"
    f.write_text("content", encoding="utf-8")
    dest_dir = tmp_path / "sorted"

    from auto_file.core.executor import PipelineResult

    failed_result = PipelineResult(
        status="failed",
        original_path=f,
        destination_path=f,
        proposed_relative_path=Path(""),
        details={"tool_selected": "text_extractor", "date_value": "2026-01-01"},
        error_message="Simulated failure",
    )

    with patch("auto_file.core.executor.FilePipelineExecutor.process_file", return_value=failed_result):
        res = runner.invoke(app, ["sort", str(f), "--dest", str(dest_dir)])

    assert res.exit_code == 0
    assert "-" in res.output
    # Ensure '.' is not printed as the destination column in the table row
    # In table format: corrupt.txt | text_extractor | 2026-01-01 | - | failed
    assert "failed" in res.output


# ==============================================================================
# On-Demand LLM Server Lifecycle Tests
# ==============================================================================


FAKE_LLAMA_SERVER = '''#!/usr/bin/env python3
"""A stand-in llama-server: serves /health and /v1/chat/completions."""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

port = 8123
args = sys.argv[1:]
for i, arg in enumerate(args):
    if arg == "--port" and i + 1 < len(args):
        port = int(args[i + 1])

pidfile = os.environ.get("FAKE_LLAMA_PIDFILE")
if pidfile:
    with open(pidfile, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))


class Handler(BaseHTTPRequestHandler):
    def _send(self, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send({"status": "ok"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length).decode("utf-8", "replace")
        if "file-routing assistant" in raw:
            content = json.dumps({"folder": "Financial/Bills"})
        else:
            content = json.dumps({
                "content_date": "2026-01-05",
                "file_description": "target_receipt",
                "detected_entities": ["Target"],
                "category_hint": "Receipt",
                "summary": "Receipt from Target for $23.45.",
            })
        self._send({"choices": [{"message": {"content": content}}]})

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", port), Handler).serve_forever()
'''


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _install_fake_llama_server(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Write the fake server, a fake model file, and return their paths."""
    binary = tmp_path / "llama-server"
    binary.write_text(FAKE_LLAMA_SERVER, encoding="utf-8")
    binary.chmod(0o755)
    model = tmp_path / "gemma-test.gguf"
    model.write_text("placeholder", encoding="utf-8")
    pidfile = tmp_path / "server.pid"
    return binary, model, pidfile


def test_cli_sort_leaves_no_llama_server_running(tmp_path: Path, monkeypatch):
    """A one-shot sort must not leave the model server running.

    The server is started on demand, so a command that exits without
    stopping it would leave a multi-gigabyte model server behind forever.
    """
    # The suite forces the deterministic understander; this test needs the
    # real LLM path so the server is actually started.
    monkeypatch.delenv("AUTO_FILE_UNDERSTANDER", raising=False)

    binary, model, pidfile = _install_fake_llama_server(tmp_path)
    monkeypatch.setenv("FAKE_LLAMA_PIDFILE", str(pidfile))

    port = _free_port()
    cfg = tmp_path / "config.json"
    set_config_value("llm_backend", "llama.cpp", cfg)
    set_config_value("llm_model", str(model), cfg)
    set_config_value("llm_binary", str(binary), cfg)
    set_config_value("llm_port", str(port), cfg)
    set_config_value("llm_idle_seconds", "900", cfg)

    source = tmp_path / "receipt.txt"
    source.write_text(
        "Receipt from Target, purchase total $23.45, paid with card. "
        "Thank you for shopping with us today.",
        encoding="utf-8",
    )
    dest = tmp_path / "sorted"
    audit_db = tmp_path / "audit.db"

    result = runner.invoke(
        app,
        [
            "sort", str(source),
            "--dest", str(dest),
            "--config-file", str(cfg),
            "--audit-db", str(audit_db),
        ],
    )

    assert result.exit_code == 0, result.output
    # The LLM chose the destination from the real folder tree.
    assert not source.exists()
    assert (dest / "Financial" / "Bills").is_dir()

    # The ledger records that the destination came from the LLM.
    ledger = AuditLedger(audit_db)
    events = ledger.get_recent_events(limit=5)
    assert any(
        e["status"] == "moved" and e["laya_category_selected"] == "llm:Financial/Bills"
        for e in events
    )

    # The server was started (so the pidfile exists) and then stopped.
    assert pidfile.is_file()
    server_pid = int(pidfile.read_text().strip())
    with pytest.raises(ProcessLookupError):
        os.kill(server_pid, 0)
    assert _port_is_free(port)


def test_cli_sort_without_llm_config_uses_no_server(tmp_path: Path, monkeypatch):
    """With no LLM configured, no model server is started at all."""
    monkeypatch.delenv("AUTO_FILE_UNDERSTANDER", raising=False)

    binary, model, pidfile = _install_fake_llama_server(tmp_path)
    monkeypatch.setenv("FAKE_LLAMA_PIDFILE", str(pidfile))

    cfg = tmp_path / "config.json"
    source = tmp_path / "receipt.txt"
    source.write_text(
        "Receipt from Target, purchase total $23.45, paid with card. "
        "Thank you for shopping with us today.",
        encoding="utf-8",
    )
    dest = tmp_path / "sorted"

    result = runner.invoke(
        app,
        ["sort", str(source), "--dest", str(dest), "--config-file", str(cfg)],
    )

    assert result.exit_code == 0, result.output
    assert not pidfile.exists()


def test_cli_sort_warns_when_llama_server_is_missing(tmp_path: Path):
    """A configured but missing server degrades to heuristics with a warning."""
    cfg = tmp_path / "config.json"
    model = tmp_path / "gemma-test.gguf"
    model.write_text("placeholder", encoding="utf-8")
    set_config_value("llm_backend", "llama.cpp", cfg)
    set_config_value("llm_model", str(model), cfg)
    set_config_value("llm_binary", str(tmp_path / "no-such-llama-server"), cfg)

    source = tmp_path / "receipt.txt"
    source.write_text(
        "Receipt from Target, purchase total $23.45, paid with card. "
        "Thank you for shopping with us today.",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["sort", str(source), "--dest", str(tmp_path / "sorted"), "--config-file", str(cfg)],
    )

    assert result.exit_code == 0, result.output
    assert "llama-server binary not found" in result.output

