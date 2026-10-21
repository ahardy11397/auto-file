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
4. **Understand** — Gemma 4 E2B-it local multimodal LLM (served on demand by llama.cpp, CPU) reads documents and scanned page images, extracting content date, detected entities, category hint, and concise description slug, with calendar validation and a deterministic heuristic fallback. The LLM is opt-in: without one, the deterministic heuristics run instead. Documents the understander cannot confidently read are left untouched in the inbox as `needs_review` instead of being renamed into a generic folder.
5. **Route** — When the LLM is available, Gemma receives the filename, the document summary, and the full folder list from the structure file, and picks exactly one existing folder; folders marked `dynamic: true` (the "by entity" folders) also accept a new final component. A pick that doesn't fit the tree — or "no folder fits" — leaves the file untouched as `needs_review`. Without an LLM, keyword routing against the taxonomy is the fallback.
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

The default install is small and needs no model. To add the optional
in-process `transformers` backend (multi-gigabyte local weights), install the
extra: `uv sync --extra llm`.

## Setup

```bash
auto-file setup
```

The interactive wizard asks for three things:

1. **Inbox** — the folder you drop unsorted files into (e.g. `~/Inbox`).
2. **Destination root** — the folder where sorted files are filed (e.g. `~/SortedFiles`).
3. **Folder structure file** — a YAML file defining where files go. If it
   doesn't exist yet, setup generates a starter file from the built-in
   defaults that you can edit.

All three are plain config settings — change them any time:

```bash
auto-file config set inbox ~/Inbox
auto-file config set dest ~/SortedFiles
auto-file config set structure ~/.config/auto-file/folder_structure.yaml
```

## Folder structure file

The destination folder tree (top-level folders, subfolders, and person
names) lives in a YAML file, not in the code — edit it and the next run
follows it. It is independent of the destination root, so you can point
any root at the same structure:

```yaml
people: [Alpha, Bravo, Charlie, Delta, Echo]
person_subfolders: [Records, Medical, Documents, Pictures, Misc]
person_root: People
roots:
  Financial:
    subfolders:
      Bank Statements: {}
      Bills: {subfolders: [Receipts, Due]}
      Receipts: {keywords: [reciept]}
      Documents: {}
      Misc: {}
  Misc: {}
```

- `people` are matched against names found in document content.
- Each root may declare `role: Financial` (etc.) when renamed, so keyword
  routing still finds it, and optional `keywords` add extra routing words.
- Each subfolder may declare optional `keywords` matched against the file's
  content.
- A subfolder marked `dynamic: true` accepts one new final folder — the
  "by entity" folders where a new vendor, company, account or case name is
  created on demand:

  ```yaml
  roots:
    Financial:
      subfolders:
        Bills:
          dynamic: true
          subfolders: [Receipts, Due]
  ```

  With this in place the LLM may answer `Financial/Bills/Acme Corp`, and the
  validator accepts it (the new name is sanitized for path safety).
- If no structure file is configured, built-in defaults (matching
  `FOLDER_STRUCTURE.md`) are used.

## Local LLM setup

Auto-file runs entirely on your machine. Nothing is downloaded at run time and
no request ever leaves the box.

By default **no LLM is used**: documents are understood with deterministic
heuristics and routed with the keyword router. To enable the local model,
configure one of two backends.

### llama.cpp (recommended)

Fast on CPU and able to read scanned page images. Build
[llama.cpp](https://github.com/ggerganov/llama.cpp) and point auto-file at
the server binary and a GGUF model:

```bash
auto-file config set llm_backend llama.cpp
auto-file config set llm_model ~/models/gemma-4-E2B-it-Q4_K_M.gguf
auto-file config set llm_binary ~/backends/llama.cpp-build/build/bin/llama-server
```

The server is started on demand, bound to `127.0.0.1` only, and stopped again
when the run ends — there is no standing network service. The vision projector
is picked up automatically from the model's folder when exactly one
`*mmproj*.gguf` sits next to it, or set it explicitly with
`auto-file config set llm_mmproj <path>`.

| Setting | Default | Meaning |
| --- | --- | --- |
| `llm_backend` | `none` | `llama.cpp`, `transformers`, or `none` (also `llama.cpp` when only `llm_model` is set) |
| `llm_model` | — | GGUF file (llama.cpp) or model id (transformers) |
| `llm_binary` | `llama-server` on `$PATH` | The llama.cpp server executable |
| `llm_mmproj` | auto-detected | Vision projector for scanned pages |
| `llm_port` | `8082` | Local port the server binds to |
| `llm_idle_seconds` | `900` | Shut the server down after this idle time |
| `min_understanding_words` | `25` | Words needed before a document counts as understood |
| `min_understanding_chars` | `120` | Characters needed before a document counts as understood |

### transformers (optional)

The in-process backend needs the model weights **already in your local
Hugging Face cache** — auto-file never downloads a model, so the weights must
be fetched separately if you want this backend:

```bash
uv sync --extra llm
auto-file config set llm_backend transformers
auto-file config set llm_model google/gemma-4-E2B-it
```

If the weights are missing, the run falls back to deterministic heuristics.

### When the model cannot read a document

A document the model cannot confidently read is left **untouched in the inbox**
and reported as `needs_review` — it is never renamed into a generic folder.
Use `auto-file sort --force` (or `auto-file watch --force`) to sort such files
anyway.

## CLI Usage

```bash
# One-time interactive setup (inbox, destination, folder structure)
auto-file setup

# Preview what would be sorted without moving files
auto-file sort ~/Downloads/statement.pdf --dry-run

# Sort a file or an entire directory (defaults to the configured inbox)
auto-file sort ~/Downloads/ --dest ~/SortedFiles

# Sort files even when the model could not confidently read them
auto-file sort ~/Downloads/ --force

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
uv sync --extra llm          # add the optional transformers backend
uv run pytest                # run the full test suite (227 tests)
```

## Project layout

```
src/auto_file/
├── cli.py                 # Typer CLI application (setup, sort, history, undo, watch, config)
├── config.py              # Configuration storage (~/.config/auto-file/config.json)
├── core/
│   ├── detector.py        # MIME/metadata detection (magic bytes, SHA-256)
│   ├── extractors/        # PDF, image, text, audio, fallback extractors
│   ├── naming.py          # slug sanitization + collision resolution
│   ├── dispatcher.py      # Laya tool dispatcher (ONNX + deterministic fallback)
│   ├── understander.py    # Gemma 4 E2B content understander (4-bit multimodal)
│   ├── router.py          # keyword routing against the active Taxonomy
│   ├── taxonomy.py        # YAML folder-structure loader + built-in defaults
│   ├── executor.py        # pipeline orchestrator (detect -> move -> audit)
│   └── watcher.py         # watchdog daemon with file write debounce
└── storage/
    └── audit.py           # SQLite audit ledger + rollback engine
```

## Running the watcher continuously

The inbox watcher is meant to run as a long-lived service. On machines
with systemd user services, install a unit like:

```ini
# ~/.config/systemd/user/auto-file-watch.service
[Unit]
Description=Auto-File inbox watcher
After=local-fs.target

[Service]
ExecStart=%h/projects/auto-file/.venv/bin/auto-file watch
WorkingDirectory=%h/projects/auto-file
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Then: `systemctl --user daemon-reload && systemctl --user enable --now auto-file-watch.service`
(plus `loginctl enable-linger` so it runs without an active desktop session).
The watcher reads the same config (inbox, destination, structure file) as
`sort`, and safely ignores already-sorted areas of the destination —
including when the inbox itself lives inside the destination root.

## Design docs

- `docs/superpowers/specs/2026-10-09-auto-file-system-design.md` — original full design specification
- `docs/superpowers/specs/2026-10-18-config-driven-taxonomy-design.md` — config-driven folder structure (current routing behavior)
- `docs/superpowers/plans/2026-10-12-auto-file-system.md` — task-by-task implementation plan
- `IDEA.md` — the original idea
