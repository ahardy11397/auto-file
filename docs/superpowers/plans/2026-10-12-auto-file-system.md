# Auto-File System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated, 100% local file sorting, renaming, and organization system using Laya decision models and Gemma 4 E2B multimodal understanding with full SQLite audit logging and undo capabilities.

**Architecture:** A modular 6-stage pipeline (`Detect` -> `Dispatch` -> `Extract` -> `Understand` -> `Route` -> `Execute & Audit`) orchestrating `onnxruntime` for zero-drift Laya classification, 4-bit quantized Gemma 4 E2B for semantic description and date extraction, and an atomic SQLite-backed file movement engine with CLI and folder-watcher interfaces.

**Tech Stack:** Python 3.12+ managed with `uv`, `typer`, `rich`, `onnxruntime`, `torch`, `transformers`, `accelerate`, `bitsandbytes`, `pypdf`, `pypdfium2`, `pillow`, `puremagic`, `mutagen`, `watchdog`, and `pytest`.

**Spec:** [`docs/superpowers/specs/2026-10-09-auto-file-system-design.md`](file:///mnt/ssd/projects/auto-file/docs/superpowers/specs/2026-10-09-auto-file-system-design.md)

## Global Constraints

- 100% local execution: no outbound network calls, telemetry, or external API usage during file processing.
- Date naming format: strictly `YYYY-MM-DD_<file_description>.<ext>`. Content date takes precedence over filesystem modification/creation date.
- Slugs: lowercased, ASCII alphanumerics and underscores only (`[a-z0-9_]`), max 64 characters. Original file extension preserved in lowercase.
- Deduplication & collisions: identical SHA-256 at destination skips move; differing SHA-256 appends numbered suffix (`_1`, `_2`).
- Reversibility: every completed file move must be recorded in SQLite audit ledger and be fully reversible via `auto-file undo`.

## Review Focus

- Extension-less or misnamed files (e.g. PDF named `.txt`): detector must rely on magic byte signatures so extraction never crashes on wrong parser.
- Files actively being written or locked by an external process during watch mode: watcher must debounce and verify size stability before processing.
- Scanned PDF documents with no selectable text: PDF extractor must detect empty text and render page 1 as an image for Gemma visual comprehension.
- Destructive collision prevention: existing files in destination must never be overwritten, regardless of casing or collision count.
- Rollback validation: undo must verify target SHA-256 matches the recorded database hash before moving back, aborting if modified by the user.

---

### Task 1: Project Scaffolding & Packaging Setup

**Files:**
- Create: `pyproject.toml`
- Create: `src/auto_file/__init__.py`
- Create: `tests/__init__.py`
- Test: `tests/test_sanity.py`

**Interfaces:**
- Consumes: None
- Produces: Package `auto_file` installable in development mode via `uv pip install -e .`

- [ ] **Step 1: Write the failing sanity test**

```python
# tests/test_sanity.py
import auto_file

def test_package_metadata():
    assert auto_file.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sanity.py`
Expected: FAIL with ModuleNotFoundError or AssertionError

- [ ] **Step 3: Implement `pyproject.toml` and `src/auto_file/__init__.py`**

Define project dependencies in `pyproject.toml` (`typer`, `rich`, `pypdf`, `pillow`, `puremagic`, `watchdog`, `pytest`) and export `__version__ = "0.1.0"`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_sanity.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "chore: scaffold project structure and packaging configuration"
```

---

### Task 2: File Detector & Metadata Extraction

**Files:**
- Create: `src/auto_file/core/detector.py`
- Test: `tests/test_detector.py`

**Interfaces:**
- Consumes: Filesystem path (`Path`)
- Produces: `FileMetadata(path: Path, mime_type: str, extension: str, size_bytes: int, ctime: datetime, mtime: datetime, sha256: str)`

- [ ] **Step 1: Write the failing detector tests**

```python
# tests/test_detector.py
from pathlib import Path
from auto_file.core.detector import detect_file_metadata, FileMetadata

def test_detect_text_file(tmp_path: Path):
    f = tmp_path / "sample.txt"
    f.write_text("Hello world", encoding="utf-8")
    meta = detect_file_metadata(f)
    assert isinstance(meta, FileMetadata)
    assert meta.extension == ".txt"
    assert "text" in meta.mime_type
    assert meta.size_bytes == 11
    assert len(meta.sha256) == 64

def test_detect_misnamed_file(tmp_path: Path):
    # PDF magic signature with .txt extension
    f = tmp_path / "fake.txt"
    f.write_bytes(b"%PDF-1.4\n%test\n")
    meta = detect_file_metadata(f)
    assert meta.mime_type == "application/pdf"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_detector.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `detect_file_metadata(path: Path) -> FileMetadata` in `src/auto_file/core/detector.py`**

Use `puremagic.from_file` with fallback to `mimetypes.guess_type` and compute SHA-256 via `hashlib.sha256`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_detector.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/core/detector.py tests/test_detector.py
git commit -m "feat: implement file metadata and MIME detection"
```

---

### Task 3: Content Extractors (PDF, Image, Text, Audio & Fallback)

**Files:**
- Create: `src/auto_file/core/extractors/base.py`
- Create: `src/auto_file/core/extractors/pdf.py`
- Create: `src/auto_file/core/extractors/image.py`
- Create: `src/auto_file/core/extractors/text.py`
- Create: `src/auto_file/core/extractors/audio.py`
- Create: `src/auto_file/core/extractors/__init__.py`
- Test: `tests/test_extractors.py`

**Interfaces:**
- Consumes: `FileMetadata`
- Produces: `ExtractedContent(text_content: str | None, image_content: Image.Image | None, exif_date: str | None, metadata_hints: dict)`

- [ ] **Step 1: Write the failing extractor tests**

```python
# tests/test_extractors.py
from pathlib import Path
from PIL import Image
from auto_file.core.detector import detect_file_metadata
from auto_file.core.extractors import get_extractor_for_tool

def test_text_extractor(tmp_path: Path):
    f = tmp_path / "notes.md"
    f.write_text("# Meeting Notes\nDiscussed budget.", encoding="utf-8")
    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("text_extractor")
    content = extractor.extract(meta)
    assert "Meeting Notes" in content.text_content

def test_image_extractor_exif_date(tmp_path: Path):
    f = tmp_path / "photo.jpg"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(f)
    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("image_extractor")
    content = extractor.extract(meta)
    assert content.image_content is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_extractors.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement extractor hierarchy in `src/auto_file/core/extractors/`**

Implement `BaseExtractor` protocol, `PDFExtractor` (with scanned fallback detection), `ImageExtractor` (with EXIF tag 36867/DateTimeOriginal parsing), `TextExtractor`, and registry helper `get_extractor_for_tool(tool_name: str)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_extractors.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/core/extractors/ tests/test_extractors.py
git commit -m "feat: implement PDF, image, text, and audio content extractors"
```

---

### Task 4: Filename Sanitizer, Slug Generator & Collision Resolver

**Files:**
- Create: `src/auto_file/core/naming.py`
- Test: `tests/test_naming.py`

**Interfaces:**
- Consumes: `date_str: str`, `raw_description: str`, `original_extension: str`, `destination_dir: Path`, `file_sha256: str`
- Produces: `ResolvedDestination(target_path: Path, is_duplicate: bool)`

- [ ] **Step 1: Write the failing naming tests**

```python
# tests/test_naming.py
from pathlib import Path
from auto_file.core.naming import sanitize_slug, resolve_target_filename

def test_sanitize_slug():
    assert sanitize_slug("Chase Bank Statement - Jan 2026!") == "chase_bank_statement_jan_2026"
    assert len(sanitize_slug("a" * 100)) == 64

def test_resolve_collision_different_hash(tmp_path: Path):
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()
    existing = dest_dir / "2026-01-15_statement.pdf"
    existing.write_bytes(b"first file content")
    
    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="statement",
        extension=".pdf",
        destination_dir=dest_dir,
        file_sha256="different_hash_value"
    )
    assert resolved.target_path.name == "2026-01-15_statement_1.pdf"
    assert not resolved.is_duplicate

def test_resolve_collision_identical_hash(tmp_path: Path):
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()
    existing = dest_dir / "2026-01-15_statement.pdf"
    content = b"same content"
    existing.write_bytes(content)
    import hashlib
    sha = hashlib.sha256(content).hexdigest()
    
    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="statement",
        extension=".pdf",
        destination_dir=dest_dir,
        file_sha256=sha
    )
    assert resolved.is_duplicate
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_naming.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `sanitize_slug` and `resolve_target_filename` in `src/auto_file/core/naming.py`**

Implement regex slug cleaning, 64-character truncation, numbered collision looping, and SHA-256 duplicate detection.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_naming.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/core/naming.py tests/test_naming.py
git commit -m "feat: implement filename sanitization and collision resolution"
```

---

### Task 5: SQLite Audit Ledger & Rollback Engine

**Files:**
- Create: `src/auto_file/storage/audit.py`
- Test: `tests/test_audit.py`

**Interfaces:**
- Consumes: DB path, run records, file event records
- Produces: `AuditLedger` class with `start_run()`, `record_event()`, `get_history()`, and `rollback_run()`

- [ ] **Step 1: Write the failing audit tests**

```python
# tests/test_audit.py
from pathlib import Path
from auto_file.storage.audit import AuditLedger

def test_audit_lifecycle_and_rollback(tmp_path: Path):
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
        status="moved"
    )
    
    # Test undo
    events_undone = ledger.rollback_run(run_id)
    assert len(events_undone) == 1
    assert src.exists()
    assert not dest.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_audit.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `AuditLedger` in `src/auto_file/storage/audit.py`**

Create SQLite tables (`runs`, `file_events`), handle transactional atomic logging, and implement `rollback_run(run_id: str | None = None)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_audit.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/storage/audit.py tests/test_audit.py
git commit -m "feat: implement SQLite audit ledger and rollback engine"
```

---

### Task 6: Laya Decision Runner & Taxonomical Router

**Files:**
- Create: `src/auto_file/core/dispatcher.py`
- Create: `src/auto_file/core/router.py`
- Test: `tests/test_router.py`

**Interfaces:**
- Consumes: File metadata, entity list, summary, taxonomy tree from `FOLDER_STRUCTURE.md`
- Produces: `dispatch_tool(metadata) -> str`, `route_destination(summary, entities) -> Path`

- [ ] **Step 1: Write the failing router and dispatcher tests**

```python
# tests/test_router.py
from pathlib import Path
from auto_file.core.router import TaxonomyRouter

def test_route_person_medical():
    router = TaxonomyRouter()
    # Route Alpha with medical record entity
    subpath = router.resolve_destination(
        entities=["Alpha"],
        category_hint="Medical Record",
        summary="Dr visit receipt for Alpha"
    )
    assert subpath == Path("People/Alpha/Medical")

def test_route_financial_bank_statement():
    router = TaxonomyRouter()
    subpath = router.resolve_destination(
        entities=["Chase Bank", "1234"],
        category_hint="Bank Statement",
        summary="Chase bank account statement"
    )
    assert subpath == Path("Financial/Bank Statements/Chase_Bank")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_router.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `LayaDispatcher` and `TaxonomyRouter`**

Load taxonomy structure directly representing `FOLDER_STRUCTURE.md`, interface with Laya ONNX runtime model when weights are present, and provide deterministic fallback matching logic for offline unit testing without GPU requirements.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_router.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/core/dispatcher.py src/auto_file/core/router.py tests/test_router.py
git commit -m "feat: implement Laya dispatcher and taxonomy router"
```

---

### Task 7: Gemma 4 E2B Multimodal Understander

**Files:**
- Create: `src/auto_file/core/understander.py`
- Test: `tests/test_understander.py`

**Interfaces:**
- Consumes: `ExtractedContent`
- Produces: `UnderstandingResult(content_date: str | None, file_description: str, detected_entities: list[str], category_hint: str, summary: str)`

- [ ] **Step 1: Write the failing understander tests**

```python
# tests/test_understander.py
from auto_file.core.extractors.base import ExtractedContent
from auto_file.core.understander import GemmaUnderstander, parse_llm_json_response

def test_parse_valid_json_response():
    raw_output = '```json\n{"content_date": "2026-02-14", "file_description": "chase_statement", "detected_entities": ["Chase"], "category_hint": "Bank Statement", "summary": "Bank statement"}\n```'
    result = parse_llm_json_response(raw_output)
    assert result.content_date == "2026-02-14"
    assert result.file_description == "chase_statement"
    assert "Chase" in result.detected_entities

def test_parse_malformed_json_fallback():
    raw_output = 'I think this is an invoice from Alpha on March 1st.'
    result = parse_llm_json_response(raw_output)
    assert result.file_description != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_understander.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `GemmaUnderstander` in `src/auto_file/core/understander.py`**

Implement JSON response parsing, prompt generation for text and image inputs, lazy model initialization for `google/gemma-4-E2B-it` with 4-bit `BitsAndBytesConfig`, and safe mock execution mode for fast testing.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_understander.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/core/understander.py tests/test_understander.py
git commit -m "feat: implement Gemma 4 E2B multimodal understander"
```

---

### Task 8: Pipeline Orchestrator & Executor

**Files:**
- Create: `src/auto_file/core/executor.py`
- Test: `tests/test_executor.py`

**Interfaces:**
- Consumes: Input file path, destination root directory, dry-run flag, `AuditLedger`
- Produces: `PipelineResult(status: str, original_path: Path, destination_path: Path, details: dict)`

- [ ] **Step 1: Write the failing pipeline integration test**

```python
# tests/test_executor.py
from pathlib import Path
from auto_file.core.executor import FilePipelineExecutor
from auto_file.storage.audit import AuditLedger

def test_pipeline_dry_run_does_not_move_file(tmp_path: Path):
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()
    
    test_file = source_dir / "statement.txt"
    test_file.write_text("Bank statement for Chase account", encoding="utf-8")
    
    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)
    
    result = executor.process_file(test_file, dry_run=True)
    assert result.status == "preview"
    assert test_file.exists()
    assert not (target_dir / result.proposed_relative_path).exists()

def test_pipeline_live_move(tmp_path: Path):
    source_dir = tmp_path / "inbox"
    source_dir.mkdir()
    target_dir = tmp_path / "sorted"
    target_dir.mkdir()
    
    test_file = source_dir / "statement.txt"
    test_file.write_text("Bank statement for Chase account", encoding="utf-8")
    
    ledger = AuditLedger(tmp_path / "audit.db")
    executor = FilePipelineExecutor(target_root=target_dir, audit_ledger=ledger)
    
    result = executor.process_file(test_file, dry_run=False)
    assert result.status == "moved"
    assert not test_file.exists()
    assert (target_dir / result.proposed_relative_path).exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_executor.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `FilePipelineExecutor` in `src/auto_file/core/executor.py`**

Wire together Detector -> Dispatcher -> Extractor -> Understander -> Router -> Naming -> Move -> Audit.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_executor.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/core/executor.py tests/test_executor.py
git commit -m "feat: implement end-to-end pipeline executor"
```

---

### Task 9: CLI Interface (`sort`, `history`, `undo`, `config`)

**Files:**
- Create: `src/auto_file/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: Command-line arguments
- Produces: Console application entrypoint registered in `pyproject.toml` (`auto-file = "auto_file.cli:app"`)

- [ ] **Step 1: Write the failing CLI tests**

```python
# tests/test_cli.py
from typer.testing import CliRunner
from auto_file.cli import app

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "sort" in result.output
    assert "history" in result.output
    assert "undo" in result.output

def test_cli_dry_run_sort(tmp_path):
    f = tmp_path / "doc.txt"
    f.write_text("Medical record for Alpha")
    result = runner.invoke(app, ["sort", str(f), "--dry-run", "--dest", str(tmp_path / "sorted")])
    assert result.exit_code == 0
    assert f.exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `app` in `src/auto_file/cli.py`**

Implement Typer commands with Rich table formatting for preview, history display, undo invocations, and config management.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/cli.py tests/test_cli.py
git commit -m "feat: implement CLI interface with sort, history, undo, and config commands"
```

---

### Task 10: Watcher Daemon (`auto-file watch`)

**Files:**
- Create: `src/auto_file/core/watcher.py`
- Modify: `src/auto_file/cli.py`
- Test: `tests/test_watcher.py`

**Interfaces:**
- Consumes: Inbox folder path, target root, debounce seconds
- Produces: `FolderWatcher` class that continuously triggers `FilePipelineExecutor`

- [ ] **Step 1: Write the failing watcher tests**

```python
# tests/test_watcher.py
import time
from pathlib import Path
from auto_file.core.watcher import FolderWatcher
from auto_file.core.executor import FilePipelineExecutor
from auto_file.storage.audit import AuditLedger

def test_watcher_detects_and_sorts_file(tmp_path: Path):
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
        f.write_text("Alpha dental medical appointment note")
        time.sleep(1.5)
        # File should have been processed and moved out of inbox
        assert not f.exists()
    finally:
        watcher.stop()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_watcher.py`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement `FolderWatcher` in `src/auto_file/core/watcher.py` and register `auto-file watch` command in `src/auto_file/cli.py`**

Use `watchdog.observers.Observer` with `FileSystemEventHandler`. Implement file stability check (ensuring byte size is stable across interval before invoking pipeline).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_watcher.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/auto_file/core/watcher.py src/auto_file/cli.py tests/test_watcher.py
git commit -m "feat: implement background folder watcher daemon"
```
