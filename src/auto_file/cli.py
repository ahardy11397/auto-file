"""Command-line interface for the Auto-File System.

Provides commands for sorting files, inspecting run history,
rolling back operations, and configuring default preferences.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import signal
import time
from typing import Any, Optional

from rich.console import Console
from rich.table import Table
import typer

from auto_file import __version__
from auto_file.config import (
    get_audit_db_path,
    get_config_value,
    get_default_dest,
    get_default_source,
    get_structure_path,
    load_config,
    set_config_value,
)
from auto_file.core.executor import FilePipelineExecutor, PipelineResult
from auto_file.core.taxonomy import load_taxonomy, taxonomy_to_yaml
from auto_file.core.watcher import FolderWatcher
from auto_file.storage.audit import (
    AuditLedger,
    RollbackError,
)

app = typer.Typer(
    help="Auto-File System: Automated local file organizer",
    add_completion=False,
)
console = Console()

DEFAULT_STRUCTURE_FILE = Path.home() / ".config" / "auto-file" / "folder_structure.yaml"


def _default_llm_binary() -> str:
    """Locate a llama-server binary: PATH first, then a local llama.cpp build."""
    found = shutil.which("llama-server")
    if found:
        return found
    return str(Path.home() / "backends" / "llama.cpp-build" / "build" / "bin" / "llama-server")


def _guess_mmproj(model: str) -> str | None:
    """Find the vision projector next to the model file, if there is one."""
    model_dir = Path(model).expanduser().parent
    if not model_dir.is_dir():
        return None
    candidates = sorted(model_dir.glob("*mmproj*.gguf"))
    return str(candidates[0]) if len(candidates) == 1 else None


def _llm_settings(config_file: Path | None) -> dict[str, Any]:
    """Resolve the LLM configuration from the config file.

    Returns a dict with:
      backend  — 'llama.cpp', 'transformers' or 'none'
      server   — on-demand llama.cpp server config (llama.cpp backend only)
      model    — model identifier (transformers backend only)
      warnings — human-readable problems with the configuration
    """
    warnings: list[str] = []

    backend = str(get_config_value("llm_backend", "", config_file) or "").strip().lower()
    model = get_config_value("llm_model", None, config_file)

    if not backend:
        backend = "llama.cpp" if model else "none"

    if backend == "none":
        return {"backend": "none", "server": None, "model": None, "warnings": warnings}

    if backend == "transformers":
        return {
            "backend": "transformers",
            "server": None,
            "model": str(model) if model else "google/gemma-4-E2B-it",
            "warnings": warnings,
        }

    if backend != "llama.cpp":
        warnings.append(
            f"Unknown llm_backend '{backend}' (expected llama.cpp, transformers or none); "
            "falling back to no LLM."
        )
        return {"backend": "none", "server": None, "model": None, "warnings": warnings}

    if not model:
        warnings.append("llm_backend is 'llama.cpp' but no llm_model is configured; using no LLM.")
        return {"backend": "none", "server": None, "model": None, "warnings": warnings}

    binary = str(get_config_value("llm_binary", None, config_file) or _default_llm_binary())
    mmproj = get_config_value("llm_mmproj", None, config_file)
    if not mmproj:
        mmproj = _guess_mmproj(str(model))

    if not Path(binary).expanduser().is_file():
        warnings.append(
            f"llama-server binary not found at {binary}; using deterministic heuristics instead."
        )
        return {"backend": "none", "server": None, "model": None, "warnings": warnings}
    if not Path(str(model)).expanduser().is_file():
        warnings.append(f"LLM model file not found at {model}; using deterministic heuristics instead.")
        return {"backend": "none", "server": None, "model": None, "warnings": warnings}
    if mmproj and not Path(str(mmproj)).expanduser().is_file():
        warnings.append(
            f"Vision projector not found at {mmproj}; the server will run without vision support."
        )
        mmproj = None

    server = {
        "binary": binary,
        "model": str(model),
        "mmproj": str(mmproj) if mmproj else None,
        "port": int(get_config_value("llm_port", 8082, config_file)),
        "idle_seconds": int(get_config_value("llm_idle_seconds", 900, config_file)),
    }
    return {"backend": "llama.cpp", "server": server, "model": None, "warnings": warnings}


def _resolved_structure(config_file: Path | None) -> Path | None:
    """Return the configured structure file path, validating it if set."""
    structure_path = get_structure_path(config_file)
    if structure_path is None:
        return None
    try:
        load_taxonomy(structure_path)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]Error: invalid folder structure file: {exc}[/red]")
        raise typer.Exit(code=1)
    return structure_path


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show auto-file version and exit.",
        is_eager=True,
    ),
) -> None:
    """Auto-File System: 100% local, privacy-first automated file organizer."""
    if version:
        console.print(f"auto-file v{__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command()
def sort(
    path: Optional[Path] = typer.Argument(
        None,
        help="Path to source file or directory to organize (defaults to configured inbox).",
        exists=False,
    ),
    dest: Optional[Path] = typer.Option(
        None,
        "--dest",
        "-d",
        help="Destination root directory for organized files.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview proposed destination and actions without modifying disk.",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Recursively process subdirectories if path is a directory.",
    ),
    audit_db: Optional[Path] = typer.Option(
        None,
        "--audit-db",
        help="Path to SQLite audit ledger database.",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        help="Path to custom config JSON file.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Sort files even when they could not be confidently understood.",
    ),
) -> None:
    """Sort and organize a single file or an entire directory."""
    source_path = path or get_default_source(config_file)
    if source_path is None:
        console.print(
            "[red]Error: Source path not specified. "
            "Provide a path or run 'auto-file setup' to configure an inbox.[/red]"
        )
        raise typer.Exit(code=1)

    if not source_path.exists():
        console.print(f"[red]Error: Source path does not exist: {source_path}[/red]")
        raise typer.Exit(code=1)

    target_dest = dest or get_default_dest(config_file)
    if target_dest is None:
        console.print(
            "[red]Error: Destination directory not specified. "
            "Provide --dest or run 'auto-file setup' to configure defaults.[/red]"
        )
        raise typer.Exit(code=1)

    resolved_audit_db = get_audit_db_path(config_file, audit_db)
    ledger = AuditLedger(resolved_audit_db)
    llm = _llm_settings(config_file)
    for warning in llm["warnings"]:
        console.print(f"[yellow]Warning: {warning}[/yellow]")
    executor = FilePipelineExecutor(
        target_root=target_dest,
        audit_ledger=ledger,
        structure=_resolved_structure(config_file),
        llm_server=llm["server"],
        llm_backend=llm["backend"],
        llm_model=llm["model"],
        min_understanding_words=int(
            get_config_value("min_understanding_words", 25, config_file)
        ),
        min_understanding_chars=int(
            get_config_value("min_understanding_chars", 120, config_file)
        ),
    )

    try:
        results: list[PipelineResult] = []
        if source_path.is_file():
            results = [executor.process_file(source_path, dry_run=dry_run, force=force)]
        elif source_path.is_dir():
            results = executor.process_directory(
                source_path,
                dry_run=dry_run,
                recursive=recursive,
                force=force,
            )
        else:
            console.print(f"[red]Error: Unsupported file path type: {source_path}[/red]")
            raise typer.Exit(code=1)
    finally:
        # Never leave a model server running after a one-shot command.
        executor.shutdown()

    table = Table(
        title="Auto-File Organization Summary" if not dry_run else "Auto-File Organization Preview",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Source File", style="white", overflow="fold")
    table.add_column("Tool", style="magenta", no_wrap=True)
    table.add_column("Date", style="green", no_wrap=True)
    table.add_column("Proposed Destination", style="blue", overflow="fold")
    table.add_column("Status", style="bold", no_wrap=True)

    for res in results:
        status_lower = res.status.lower()
        if status_lower == "moved":
            status_style = "[green]moved[/green]"
        elif status_lower == "preview":
            status_style = "[yellow]preview[/yellow]"
        elif status_lower == "duplicate_skipped":
            status_style = "[cyan]duplicate_skipped[/cyan]"
        elif status_lower == "needs_review":
            status_style = "[magenta]needs_review[/magenta]"
        elif status_lower == "failed":
            status_style = "[red]failed[/red]"
        else:
            status_style = res.status

        if status_lower == "failed":
            proposed_dest = "-"
        elif status_lower == "needs_review":
            # The file was left untouched in the inbox.
            proposed_dest = "[dim]left in inbox[/dim]"
        else:
            proposed_dest = str(res.proposed_relative_path)

        table.add_row(
            res.original_path.name,
            str(res.details.get("tool_selected", "-")),
            str(res.details.get("date_value", "-")),
            proposed_dest,
            status_style,
        )

    console.print(table)

    # Print summary counts
    moved_count = sum(1 for r in results if r.status == "moved")
    preview_count = sum(1 for r in results if r.status == "preview")
    skipped_count = sum(1 for r in results if r.status == "duplicate_skipped")
    review_count = sum(1 for r in results if r.status == "needs_review")
    failed_count = sum(1 for r in results if r.status == "failed")

    summary_parts = []
    if moved_count:
        summary_parts.append(f"{moved_count} moved")
    if preview_count:
        summary_parts.append(f"{preview_count} previewed")
    if skipped_count:
        summary_parts.append(f"{skipped_count} duplicate skipped")
    if review_count:
        summary_parts.append(f"{review_count} left for review")
    if failed_count:
        summary_parts.append(f"{failed_count} failed")

    summary_str = ", ".join(summary_parts) if summary_parts else "0 files processed"
    console.print(f"[bold]Total processed:[/bold] {len(results)} file(s) ({summary_str})")


@app.command()
def history(
    limit: int = typer.Option(
        25,
        "--limit",
        "-n",
        help="Maximum number of records to display.",
    ),
    runs: bool = typer.Option(
        False,
        "--runs",
        help="Show run summaries instead of individual file events.",
    ),
    audit_db: Optional[Path] = typer.Option(
        None,
        "--audit-db",
        help="Path to SQLite audit ledger database.",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        help="Path to custom config JSON file.",
    ),
    run_id: Optional[str] = typer.Option(
        None,
        "--run-id",
        help="Inspect individual file events for a specific run ID.",
    ),
) -> None:
    """View recent file moves: original name, where it was filed, and status."""
    resolved_audit_db = get_audit_db_path(config_file, audit_db)
    ledger = AuditLedger(resolved_audit_db)

    if run_id:
        events = ledger.get_events_for_run(run_id)
        if not events:
            console.print(f"[yellow]No events found for run ID: {run_id}[/yellow]")
            return

        table = Table(
            title=f"File Events for Run {run_id}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("File", style="white")
        table.add_column("Destination", style="blue")
        table.add_column("Tool", style="magenta")
        table.add_column("Date", style="green")
        table.add_column("Status", style="bold")

        for event in events:
            status_lower = event["status"].lower()
            if status_lower == "moved":
                status_style = "[green]moved[/green]"
            elif status_lower == "rolled_back":
                status_style = "[yellow]rolled_back[/yellow]"
            elif status_lower == "failed":
                status_style = "[red]failed[/red]"
            else:
                status_style = event["status"]

            table.add_row(
                Path(event["original_path"]).name,
                str(event["destination_path"]),
                str(event.get("laya_tool_selected", "-")),
                str(event.get("date_value", "-")),
                status_style,
            )
        console.print(table)
        return

    if runs:
        history_records = ledger.get_history(limit=limit)
        if not history_records:
            console.print("[yellow]No run history found in audit ledger.[/yellow]")
            return

        table = Table(
            title="Audit Run History",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Run ID", style="cyan", overflow="fold")
        table.add_column("Started At", style="white", overflow="fold")
        table.add_column("Mode", style="magenta", no_wrap=True)
        table.add_column("Source Root", style="dim", overflow="fold")
        table.add_column("Target Root", style="dim", overflow="fold")
        table.add_column("Total", justify="right")
        table.add_column("Success", justify="right", style="green")
        table.add_column("Failed", justify="right", style="red")

        for run in history_records:
            table.add_row(
                str(run["run_id"]),
                str(run["started_at"]),
                str(run["mode"]),
                str(run["source_root"]),
                str(run["target_root"]),
                str(run["total_files"]),
                str(run["successful_files"]),
                str(run["failed_files"]),
            )

        console.print(table)
        return

    events = ledger.get_recent_events(limit=limit)
    if not events:
        console.print("[yellow]No file history found in audit ledger.[/yellow]")
        console.print("[dim]Tip: 'auto-file history --runs' shows run summaries.[/dim]")
        return

    console.print("[bold]Recent File Moves[/bold] (newest first)")
    for event in events:
        status_lower = event["status"].lower()
        if status_lower == "moved":
            status_style = "[green]moved[/green]"
        elif status_lower == "rolled_back":
            status_style = "[yellow]rolled_back[/yellow]"
        elif status_lower == "duplicate_skipped":
            status_style = "[cyan]duplicate_skipped[/cyan]"
        elif status_lower == "needs_review":
            status_style = "[magenta]needs_review[/magenta]"
        elif status_lower == "failed":
            status_style = "[red]failed[/red]"
        else:
            status_style = event["status"]

        console.print(
            f"{event.get('timestamp', '-')}  {status_style}  "
            f"{Path(event['original_path']).name} -> {event['destination_path']}",
            soft_wrap=True,
        )


@app.command()
def undo(
    run_id: Optional[str] = typer.Option(
        None,
        "--run-id",
        help="Specific run identifier to roll back.",
    ),
    last: bool = typer.Option(
        False,
        "--last",
        "-l",
        help="Roll back the most recent completed run.",
    ),
    audit_db: Optional[Path] = typer.Option(
        None,
        "--audit-db",
        help="Path to SQLite audit ledger database.",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        help="Path to custom config JSON file.",
    ),
) -> None:
    """Roll back previous file movement operations safely."""
    if run_id and last:
        console.print(
            "[yellow]Cannot specify both --run-id and --last. Please specify either a specific --run-id or use --last for the most recent run.[/yellow]"
        )
        raise typer.Exit(code=1)

    resolved_audit_db = get_audit_db_path(config_file, audit_db)
    if str(resolved_audit_db) != ":memory:" and not resolved_audit_db.is_file():
        console.print(f"[yellow]Audit ledger database does not exist: {resolved_audit_db}[/yellow]")
        raise typer.Exit(code=1)

    ledger = AuditLedger(resolved_audit_db)

    try:
        # If run_id is None, rollback_run defaults to the most recent run with moved files
        undone = ledger.rollback_run(run_id=run_id)
        if not undone:
            console.print("[yellow]No moved files found to roll back.[/yellow]")
            return

        table = Table(
            title="Rollback Summary",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Original Path", style="green", overflow="fold")
        table.add_column("Restored From", style="blue", overflow="fold")
        table.add_column("Status", style="bold", no_wrap=True)

        for event in undone:
            status_style = (
                "[green]rolled_back[/green]"
                if event["status"] == "rolled_back"
                else f"[yellow]{event['status']}[/yellow]"
            )
            table.add_row(
                str(event["original_path"]),
                str(event["destination_path"]),
                status_style,
            )

        console.print(table)
        console.print(f"[green]Successfully rolled back {len(undone)} file(s).[/green]")

    except RollbackError as exc:
        console.print(f"[red]Rollback failed: {exc}[/red]")
        raise typer.Exit(code=1)


@app.command()
def config(
    action_or_key: Optional[str] = typer.Argument(
        None,
        help="Action ('get', 'set') or config key.",
    ),
    param1: Optional[str] = typer.Argument(
        None,
        help="Key (if action used) or value to set.",
    ),
    param2: Optional[str] = typer.Argument(
        None,
        help="Value to set (if 'set' action used).",
    ),
    get: Optional[str] = typer.Option(
        None,
        "--get",
        "-g",
        help="Retrieve configuration value for key.",
    ),
    set: Optional[tuple[str, str]] = typer.Option(
        None,
        "--set",
        "-s",
        help="Set key and value (e.g. --set dest /path).",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Display all configuration settings.",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        help="Path to custom config JSON file.",
    ),
) -> None:
    """Manage configuration settings (default source, destination, and audit db)."""
    # 1. Flag-based --set
    if set:
        key, val = set[0], set[1]
        set_config_value(key, val, config_file)
        console.print(f"[green]Set '{key}' = '{val}'[/green]")
        return

    # 2. Flag-based --get
    if get:
        val = get_config_value(get, config_path=config_file)
        if val is None:
            console.print(f"[yellow]Key '{get}' not configured.[/yellow]")
        else:
            console.print(str(val))
        return

    # 3. Positional subcommand parsing
    if action_or_key:
        if action_or_key.lower() == "set":
            if not param1 or not param2:
                console.print("[red]Usage: auto-file config set <key> <value>[/red]")
                raise typer.Exit(code=1)
            set_config_value(param1, param2, config_file)
            console.print(f"[green]Set '{param1}' = '{param2}'[/green]")
            return

        if action_or_key.lower() == "get":
            if not param1:
                console.print("[red]Usage: auto-file config get <key>[/red]")
                raise typer.Exit(code=1)
            val = get_config_value(param1, config_path=config_file)
            if val is None:
                console.print(f"[yellow]Key '{param1}' not configured.[/yellow]")
            else:
                console.print(str(val))
            return

        # Syntax: config <key> <value> -> set
        if param1 is not None:
            set_config_value(action_or_key, param1, config_file)
            console.print(f"[green]Set '{action_or_key}' = '{param1}'[/green]")
            return

        # Syntax: config <key> -> get
        val = get_config_value(action_or_key, config_path=config_file)
        if val is None:
            console.print(f"[yellow]Key '{action_or_key}' not configured.[/yellow]")
        else:
            console.print(str(val))
        return

    # 4. Default: show all configuration settings
    current_config = load_config(config_file)
    table = Table(
        title="Auto-File Configuration",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    if not current_config:
        table.add_row("(none)", "(no settings configured)")
    else:
        for k, v in sorted(current_config.items()):
            table.add_row(str(k), str(v))

    console.print(table)
    active_audit = get_audit_db_path(config_file)
    console.print(f"[dim]Effective Audit DB: {active_audit}[/dim]")


@app.command()
def watch(
    inbox_dir: Optional[Path] = typer.Argument(
        None,
        help="Path to inbox directory to monitor for new incoming files (defaults to configured inbox).",
        exists=False,
    ),
    dest: Optional[Path] = typer.Option(
        None,
        "--dest",
        "-d",
        help="Destination root directory for organized files.",
    ),
    debounce: float = typer.Option(
        2.0,
        "--debounce",
        help="Debounce interval in seconds before processing a detected file.",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Recursively monitor subdirectories inside inbox.",
    ),
    audit_db: Optional[Path] = typer.Option(
        None,
        "--audit-db",
        help="Path to SQLite audit ledger database.",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        help="Path to custom config JSON file.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Sort files even when they could not be confidently understood.",
    ),
) -> None:
    """Watch an inbox directory continuously and organize incoming files automatically."""
    resolved_inbox = inbox_dir or get_default_source(config_file)
    if resolved_inbox is None:
        console.print(
            "[red]Error: Inbox directory not specified. "
            "Provide a directory argument or run 'auto-file setup' to configure one.[/red]"
        )
        raise typer.Exit(code=1)

    if not resolved_inbox.exists():
        console.print(f"[red]Error: Inbox directory does not exist: {resolved_inbox}[/red]")
        raise typer.Exit(code=1)

    if not resolved_inbox.is_dir():
        console.print(f"[red]Error: Inbox path is not a directory: {resolved_inbox}[/red]")
        raise typer.Exit(code=1)

    target_dest = dest or get_default_dest(config_file)
    if target_dest is None:
        console.print(
            "[red]Error: Destination directory not specified. "
            "Provide --dest or run 'auto-file setup' to configure defaults.[/red]"
        )
        raise typer.Exit(code=1)

    resolved_audit_db = get_audit_db_path(config_file, audit_db)
    ledger = AuditLedger(resolved_audit_db)
    structure_path = _resolved_structure(config_file)
    llm = _llm_settings(config_file)
    for warning in llm["warnings"]:
        console.print(f"[yellow]Warning: {warning}[/yellow]")
    executor = FilePipelineExecutor(
        target_root=target_dest,
        audit_ledger=ledger,
        structure=structure_path,
        llm_server=llm["server"],
        llm_backend=llm["backend"],
        llm_model=llm["model"],
        min_understanding_words=int(
            get_config_value("min_understanding_words", 25, config_file)
        ),
        min_understanding_chars=int(
            get_config_value("min_understanding_chars", 120, config_file)
        ),
    )

    def _on_file_processed(res: PipelineResult) -> None:
        status_lower = res.status.lower()
        if status_lower == "moved":
            status_style = "[green]moved[/green]"
        elif status_lower == "duplicate_skipped":
            status_style = "[cyan]duplicate_skipped[/cyan]"
        elif status_lower == "needs_review":
            status_style = "[magenta]needs_review — left in inbox[/magenta]"
        elif status_lower == "failed":
            status_style = "[red]failed[/red]"
        else:
            status_style = res.status

        if status_lower == "needs_review":
            destination = "[dim]left in inbox[/dim]"
        else:
            destination = f"[blue]{res.proposed_relative_path}[/blue]"
        console.print(
            f"[bold cyan]Auto-Organized:[/bold cyan] {res.original_path.name} -> "
            f"{destination} ({status_style})"
        )

    watcher = FolderWatcher(
        inbox_dir=resolved_inbox,
        executor=executor,
        debounce_seconds=debounce,
        recursive=recursive,
        on_processed=_on_file_processed,
        force=force,
    )

    console.print(
        f"[bold green]Watching directory:[/bold green] {resolved_inbox.resolve()}\n"
        f"[bold blue]Organizing into:[/bold blue] {target_dest.resolve()}\n"
        f"[dim]Structure: {structure_path or '(built-in defaults)'}\n"
        f"Debounce: {debounce}s | Recursive: {recursive} | Press Ctrl+C to stop[/dim]"
    )

    try:
        def _handle_sigterm(signum: int, frame: object) -> None:
            raise KeyboardInterrupt()

        signal.signal(signal.SIGTERM, _handle_sigterm)
    except (ValueError, AttributeError):
        pass

    watcher.start()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping watcher daemon...[/yellow]")
    finally:
        watcher.stop()
        # Never leave a model server running after the watcher stops.
        executor.shutdown()
        console.print("[green]Watcher stopped cleanly.[/green]")


@app.command()
def setup(
    inbox: Optional[Path] = typer.Option(
        None,
        "--inbox",
        "-i",
        help="Inbox folder where you drop files to sort (skips the prompt).",
    ),
    dest: Optional[Path] = typer.Option(
        None,
        "--dest",
        "-d",
        help="Destination root folder where organized files are filed (skips the prompt).",
    ),
    structure: Optional[Path] = typer.Option(
        None,
        "--structure",
        "-s",
        help="Path to a YAML folder-structure file defining where files go (skips the prompt).",
    ),
    generate_structure: Optional[bool] = typer.Option(
        None,
        "--generate-structure/--no-generate-structure",
        help="Write a starter folder-structure file when it does not exist yet.",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        help="Path to custom config JSON file.",
    ),
) -> None:
    """Configure auto-file: inbox, destination root, and folder structure.

    Run with no options for an interactive walkthrough. Everything can be
    changed later by re-running setup or with 'auto-file config set'.
    """
    console.print("[bold]Auto-File setup[/bold]")
    console.print(
        "[dim]Drop files in the inbox; auto-file reads them, renames them, "
        "and files them under the destination root.[/dim]\n"
    )

    # 1. Inbox
    if inbox is None:
        default_inbox = get_default_source(config_file) or Path.home() / "Inbox"
        inbox = Path(typer.prompt("Inbox folder (where you drop files to sort)", default=str(default_inbox))).expanduser()
    if inbox.exists() and not inbox.is_dir():
        console.print(f"[red]Error: inbox path is not a directory: {inbox}[/red]")
        raise typer.Exit(code=1)
    if not inbox.exists():
        inbox.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Created inbox directory:[/green] {inbox}")

    # 2. Destination root
    if dest is None:
        default_dest = get_default_dest(config_file) or Path.home() / "SortedFiles"
        dest = Path(typer.prompt("Destination root (where sorted files are filed)", default=str(default_dest))).expanduser()
    if dest.exists() and not dest.is_dir():
        console.print(f"[red]Error: destination path is not a directory: {dest}[/red]")
        raise typer.Exit(code=1)
    if not dest.exists():
        dest.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Created destination directory:[/green] {dest}")

    # 3. Folder structure file
    if structure is None:
        configured = get_structure_path(config_file)
        structure = Path(
            typer.prompt(
                "Folder structure file (defines where files go)",
                default=str(configured or DEFAULT_STRUCTURE_FILE),
            )
        ).expanduser()

    structure_generated = False
    if structure.exists():
        try:
            load_taxonomy(structure)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]Error: {exc}[/red]")
            raise typer.Exit(code=1)
        console.print(f"[green]Using existing folder structure:[/green] {structure}")
    else:
        should_generate = generate_structure
        if should_generate is None:
            should_generate = typer.confirm(
                f"Folder structure file does not exist: {structure}\nGenerate a starter one you can edit?",
                default=True,
            )
        if should_generate:
            structure.parent.mkdir(parents=True, exist_ok=True)
            structure.write_text(taxonomy_to_yaml(), encoding="utf-8")
            structure_generated = True
            console.print(f"[green]Wrote starter folder structure:[/green] {structure}")
        else:
            console.print(
                "[yellow]No structure file written; built-in defaults will be used until it exists.[/yellow]"
            )

    # 4. Persist configuration
    set_config_value("inbox", str(inbox), config_file)
    set_config_value("dest", str(dest), config_file)
    set_config_value("structure", str(structure), config_file)

    table = Table(
        title="Setup complete",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("inbox", str(inbox))
    table.add_row("dest", str(dest))
    table.add_row("structure", str(structure))
    console.print(table)

    console.print(
        "\n[bold]Next steps[/bold]\n"
        "  1. Preview a sort:        auto-file sort --dry-run\n"
        "  2. Sort everything now:   auto-file sort\n"
        "  3. Watch the inbox:       auto-file watch\n"
        f"\nEdit the folder structure any time (takes effect on the next run): {structure}"
        + ("  [dim](just generated)[/dim]" if structure_generated else "")
    )
