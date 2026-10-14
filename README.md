# auto-file

Automated, 100% local file sorting, renaming, and organization system. No file, metadata, or token ever leaves the machine.

## How it works

A six-stage pipeline turns an unsorted file into a cleanly named, correctly filed, auditable move:

```
Detect → Dispatch → Extract → Understand → Route → Execute & Audit
```

1. **Detect** — MIME type (magic-byte signature via `puremagic`, fallback `mimetypes`), size, timestamps, streaming SHA-256. Misnamed files (e.g. a PDF named `.txt`) and extensionless files are identified correctly.
2. **Dispatch** — Laya decision runner (`onnxruntime` ModernBERT with deterministic heuristic fallback) picks the optimal extractor tool.
3. **Extract** — Dedicated extractors: PDF text (`pypdf`, rendered page preview for scanned docs via `pypdfium2`), image EXIF with orientation transposition (`pillow`), bounded plain text, audio metadata tags (`mutagen`), and binary fallback.
4. **Understand** — 4-bit quantized Gemma 4 E2B local multimodal LLM extracts content date, detected entities, category hint, and concise description slug, with calendar validation and safe heuristic fallback.
5. **Route** — Hierarchical taxonomy matching against `FOLDER_STRUCTURE.md` (People / Financial / Legal / Property / Manuals / Misc).
6. **Execute & Audit** — Atomic move with collision handling, verified against pre-move SHA-256 and logged to a reversible SQLite ledger.

### Naming

Files are renamed to `YYYY-MM-DD_<description>.<ext>`:

- Date comes from document content or EXIF first, filesystem mtime as fallback.
- Description is a lowercase `snake_case` slug, max 64 chars.
- Identical content at the destination (same SHA-256) is detected as a duplicate and skipped; a different file with the same name gets a `_1`, `_2` suffix. Existing files are never overwritten.

### Safety & reversibility

Every move is recorded in a SQLite audit ledger. Rollback (`auto-file undo`) verifies the file on disk still matches the recorded SHA-256 before moving it back, and aborts safely if destination files exist or hashes do not match — user data is never lost or overwritten.

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv pip install -e .
```

## CLI Usage

```bash
# Preview what would be sorted without moving files
auto-file sort ~/Downloads/statement.pdf --dry-run

# Sort a file or an entire directory
auto-file sort ~/Downloads/ --dest ~/SortedFiles

# Watch an incoming inbox folder continuously
auto-file watch ~/Inbox --dest ~/SortedFiles

# View audit history of past sorting runs
auto-file history --limit 20

# Undo the last sorting operation (safely moves files back)
auto-file undo --last

# View or set persistent configuration
auto-file config --show
auto-file config set dest ~/SortedFiles
```

## Development & Testing

```bash
uv sync                      # install dependencies
uv run pytest                # run the full test suite (152 tests)
```

## Project layout

```
src/auto_file/
├── cli.py                 # Typer CLI application (sort, history, undo, watch, config)
├── config.py              # Configuration storage (~/.config/auto-file/config.json)
├── core/
│   ├── detector.py        # MIME/metadata detection (magic bytes, SHA-256)
│   ├── extractors/        # PDF, image, text, audio, fallback extractors
│   ├── naming.py          # slug sanitization + collision resolution
│   ├── dispatcher.py      # Laya tool dispatcher (ONNX + deterministic fallback)
│   ├── understander.py    # Gemma 4 E2B content understander (4-bit multimodal)
│   ├── router.py          # taxonomy routing against FOLDER_STRUCTURE.md
│   ├── executor.py        # pipeline orchestrator (detect -> move -> audit)
│   └── watcher.py         # watchdog daemon with file write debounce
└── storage/
    └── audit.py           # SQLite audit ledger + rollback engine
```

## Design docs

- `docs/superpowers/specs/2026-10-09-auto-file-system-design.md` — full design specification
- `docs/superpowers/plans/2026-10-12-auto-file-system.md` — task-by-task implementation plan
- `FOLDER_STRUCTURE.md` — the target folder taxonomy
- `IDEA.md` — the original idea
