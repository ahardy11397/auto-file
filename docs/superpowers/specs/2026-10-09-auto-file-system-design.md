# Auto-File System Design Specification

- **Date:** 2026-10-09
- **Status:** Approved (Ready for Implementation Planning)
- **Target Repository:** `/mnt/ssd/projects/auto-file`

> **Note (2026-10-18):** Routing described here as hardcoded against
> `FOLDER_STRUCTURE.md` is now config-driven — see
> `2026-10-18-config-driven-taxonomy-design.md` for the current folder
> taxonomy, setup wizard, and watcher behavior. This document is kept as
> the original design record.

---

## 1. Executive Summary & Purpose

The **Auto-File System** (`auto-file`) is an automated, 100% offline, local file sorting, renaming, and organization tool. It leverages:
1. **Laya** (`receptron/laya` ModernBERT decision model) via local `onnxruntime` for fast, zero-drift classification (tool dispatching and hierarchical taxonomy routing).
2. **Gemma 4 E2B** (`google/gemma-4-E2B-it`) 4-bit quantized local multimodal LLM for semantic content comprehension, date extraction, and filename slug generation.

The system ensures complete privacy: no file, metadata, or token leaves the local machine. All movements are safe, transactional, collision-resistant, and recorded in a reversible SQLite audit ledger.

---

## 2. Core Requirements & User Expectations

- **Execution Modes:**
  - **CLI Batch / Single File:** On-demand scanning and sorting with `--dry-run` preview capability.
  - **Folder Watcher Daemon:** Continuous monitoring of an incoming inbox directory with write-completion debounce.
- **Naming Convention:** `YYYY-MM-DD_<file_description>.<ext>`
  - Date extracted from document content or EXIF metadata first.
  - Fallback to filesystem creation/modification date if no content date is found.
  - File description formatted as clean, lowercase `snake_case` slug (max 64 chars).
- **Target Taxonomy:** Strict hierarchical routing according to `FOLDER_STRUCTURE.md`:
  - `People/<Name>/[Records|Medical|Documents|Pictures|Misc]` for Alpha, Bravo, Charlie, Delta, Echo.
  - `Financial/[Bills|Bank Statements|Receipts|Documents|Misc]`.
  - `Legal/[Court|Misc]`.
  - `Property/[Vehicles|Real Estate|Misc]`.
  - `Manuals/<Category>`.
  - `Misc`.
- **Safety & Reversibility:**
  - Checksum validation (SHA-256) before and after move.
  - Numerical collision suffixing (`_1`, `_2`) if a distinct file already exists at the destination.
  - Deduplication: Skip moving if identical content (matching SHA-256) is already present at destination.
  - Full audit logging in SQLite enabling `auto-file undo --last` or `auto-file undo --run-id <ID>`.

---

## 3. System Architecture & Pipeline Stages

The processing pipeline runs linearly through six distinct stages:

```
[ Input File ]
      │
      ▼
1. Detect Stage ──────► File MIME, extension, size, filesystem timestamps
      │
      ▼
2. Dispatch Stage ────► Laya (ONNX): Chooses scanner tool based on file metadata
      │                 (pdf_extractor, image_extractor, text_extractor, audio_extractor, fallback)
      ▼
3. Extract Stage ─────► Runs tool: parses text, extracts EXIF, or extracts page preview
      │
      ▼
4. Understand Stage ──► Gemma 4 E2B (4-bit local): Extracts content date, detected
      │                 entities (names, institutions), and a descriptive summary
      ▼
5. Route Stage ───────► Laya (ONNX): Matches entities & summary against the taxonomy
      │                 in FOLDER_STRUCTURE.md (Top Category ➔ Subcategory)
      ▼
6. Execute & Audit ───► Resolves filename (YYYY-MM-DD_slug.ext) & collisions (_1, _2),
                        atomically moves file, and logs transaction to SQLite ledger
```

### Stage Details

### 3.1. Detect Stage (`auto_file.detector`)
- Detects MIME type using `mimetypes` and binary file header inspection (`puremagic` / magic signatures).
- Gathers file stats: byte size, file extension, `ctime` (creation/change time), and `mtime` (modification time).

### 3.2. Dispatch Stage (`auto_file.dispatcher`)
- Employs Laya (`onnxruntime`) with a discrete choice prompt:
  - Input: `{"mime_type": "...", "extension": "...", "size_bytes": ...}`
  - Choices: `["pdf_extractor", "image_extractor", "text_extractor", "audio_extractor", "fallback_extractor"]`
- Output: Exact tool name selected with confidence score.

### 3.3. Extract Stage (`auto_file.extractors`)
- **`PDFExtractor`:** Extracts text using `pypdf`. For scanned PDFs (text length < 50 characters), renders page 1 to an image via `pypdfium2` for visual inspection.
- **`ImageExtractor`:** Uses `PIL` to extract EXIF `DateTimeOriginal`. Converts image to RGB and scales to max 1024x1024 for multimodal LLM input.
- **`TextExtractor`:** Reads text/markdown/code/CSV up to 8,000 characters.
- **`AudioExtractor`:** Reads audio metadata tags (mutagen/ID3: artist, title, album, year).
- **`FallbackExtractor`:** Extracts raw header snippet and filename hints.

### 3.4. Understand Stage (`auto_file.understander`)
- Runs `google/gemma-4-E2B-it` quantized with 4-bit `bitsandbytes` (NF4), loading into GPU VRAM (~2-3 GB on GTX 1660) with CPU offload safety fallback.
- Prompt instructs the model to produce strict JSON:
  ```json
  {
    "content_date": "YYYY-MM-DD",
    "file_description": "concise_slug_phrase",
    "detected_entities": ["Alpha", "Chase"],
    "category_hint": "Bank Statement",
    "summary": "Brief 1-sentence content summary"
  }
  ```
- If `content_date` is absent or unparseable, flags `date_source = "filesystem"` and formats `mtime` as `YYYY-MM-DD`.

### 3.5. Route Stage (`auto_file.router`)
- Uses Laya ONNX in a hierarchical decision tree against `FOLDER_STRUCTURE.md`:
  - **Level 1 (Root Category):** `["People", "Financial", "Legal", "Property", "Manuals", "Misc"]`
  - **Level 2 (Branch):**
    - `People` ➔ Person choice: `["Alpha", "Bravo", "Charlie", "Delta", "Echo"]` ➔ Folder choice: `["Records", "Medical", "Docuements", "Pictures", "Misc"]`
    - `Financial` ➔ Category choice: `["Bills", "Bank Statements", "Reciepts", "Documents", "Misc"]`
    - `Legal` ➔ Category choice: `["Court", "Misc"]`
    - `Property` ➔ Category choice: `["Vehicles", "Real Estate", "Misc"]`
    - `Manuals` ➔ Category choice: `["Appliances", "Electronics", "Vehicles", "Tools", "General"]`
  - **Level 3 (Entity / Case Folder):** For entities like bank accounts, bills, or court cases, uses sanitized entity names from `detected_entities`.

### 3.6. Execute & Audit Stage (`auto_file.executor`)
- Computes SHA-256 of incoming file.
- Generates destination filename: `<date>_<description>.<ext>`.
- Resolves collisions:
  - If destination file exists with same SHA-256: registers duplicate, skips copy/move (or moves to `Duplicates/`).
  - If destination file exists with different SHA-256: appends `_<counter>` (e.g. `2026-03-15_bank_statement_1.pdf`).
- Moves file atomically.
- Records row in SQLite audit ledger.

---

## 4. SQLite Audit Ledger & Undo Engine

### Database Schema (`~/.config/auto-file/audit.db` or `./data/audit.db`)

```sql
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    mode TEXT NOT NULL,          -- 'cli_single', 'cli_batch', 'watch_daemon'
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
    date_source TEXT NOT NULL,   -- 'content' or 'filesystem'
    date_value TEXT NOT NULL,
    description TEXT NOT NULL,
    laya_tool_selected TEXT NOT NULL,
    laya_category_selected TEXT NOT NULL,
    status TEXT NOT NULL,        -- 'moved', 'rolled_back', 'failed', 'duplicate_skipped'
    error_message TEXT
);
```

### Undo Logic
- `auto-file undo --last` or `auto-file undo --run-id <run_id>`:
  1. Queries all `file_events` with `status = 'moved'` for that run in reverse chronological order.
  2. For each event, verifies that the file at `destination_path` exists and has the expected `sha256`.
  3. Verifies that `original_path` does not exist (or resolves collision).
  4. Moves the file back to `original_path`.
  5. Updates event `status = 'rolled_back'`.

---

## 5. CLI Interface & Watcher Daemon

Built using `typer` and `rich`.

```bash
# Sort a single file or directory
auto-file sort <path> [--dest <dir>] [--dry-run]

# Continuous folder watcher
auto-file watch <inbox_dir> [--dest <dir>]

# View audit history
auto-file history [--limit 25]

# Rollback sorting action
auto-file undo [--run-id <run_id> | --last]

# Configuration settings (default source, destination, model paths)
auto-file config [--get <key> | --set <key> <value>]
```

### Watcher Daemon Resilience
- Uses `watchdog.observers.Observer`.
- Debounces file events: when `FileCreatedEvent` fires, the file is monitored until size remains unchanged for 2 seconds and file locks are released before entering the pipeline.

---

## 6. Project Layout & Dependencies

Managed with `uv` in Python 3.12+:

```
auto-file/
├── FOLDER_STRUCTURE.md
├── IDEA.md
├── pyproject.toml
├── README.md
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-10-09-auto-file-system-design.md
├── src/
│   └── auto_file/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── core/
│       │   ├── detector.py
│       │   ├── dispatcher.py
│       │   ├── extractors/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── pdf.py
│       │   │   ├── image.py
│       │   │   ├── text.py
│       │   │   └── audio.py
│       │   ├── understander.py
│       │   ├── router.py
│       │   ├── executor.py
│       │   └── watcher.py
│       └── storage/
│           └── audit.py
└── tests/
    ├── test_detector.py
    ├── test_extractors.py
    ├── test_naming_and_collisions.py
    ├── test_router.py
    ├── test_audit_and_undo.py
    └── test_cli.py
```

### Dependencies
- `typer`, `rich`: CLI and formatted console output.
- `onnxruntime` (with optional `onnxruntime-gpu`): Laya decision model inference.
- `torch`, `transformers`, `accelerate`, `bitsandbytes`: Local Gemma 4 E2B 4-bit inference.
- `pypdf`, `pypdfium2`, `pillow`, `mutagen`, `puremagic`: Document, image, and audio extraction.
- `watchdog`: Cross-platform filesystem watcher.
- `pytest`: Comprehensive automated testing.

---

## 7. Verification & Testing Matrix

| Test Suite | Scope | Success Criteria |
|---|---|---|
| `test_detector` | Unit | Accurate MIME and extension detection on PDF, JPEG, TXT, and extensionless files. |
| `test_extractors` | Unit | PDF text extracted; fallback image rendered; EXIF `DateTimeOriginal` extracted. |
| `test_naming` | Unit | Slug formatting, slug length truncation, duplicate suffixing (`_1`, `_2`). |
| `test_router` | Unit | Correct hierarchical branch resolution against `FOLDER_STRUCTURE.md`. |
| `test_audit_undo` | Unit & Integration | File move logged to SQLite; `undo` safely moves file back and matches SHA-256. |
| `test_cli_dry_run` | Integration | CLI executes with `--dry-run`, outputs table, alters no files on disk. |
| `test_e2e_sort` | Integration | End-to-end sorting of synthetic test files into mock target folder hierarchy. |
