# Config-Driven Folder Structure — Design (2026-10-18)

Status: implemented.

## Intent

The original router hardcoded the entire folder taxonomy from
`FOLDER_STRUCTURE.md` (root categories, person names, subfolder names) as
Python constants, so changing where files get filed required editing code.
The goal: the folder structure lives in a user-editable config file, is
independent of the destination root, and the CLI provides a real setup
flow.

## Decisions

- **Format: YAML.** Chosen over markdown/JSON — editable by hand, supports
  nested structure cleanly.
- **Fallback: built-in defaults.** With no structure file configured, the
  router uses the built-in taxonomy matching the original
  `FOLDER_STRUCTURE.md`, so the tool always works out of the box.
- **Structure key is independent of `dest`.** Config gains a `structure`
  key (aliases `structure_file`, `folder_structure`); `sort` and `watch`
  load and validate it automatically. The same YAML can drive any
  destination root.
- **Keyword heuristics stay in code; folder names come from data.** The
  router's decision logic (which content words trigger which branch) is
  behavior; the tree is data. Folder selection is by name match (fuzzy,
  normalized) against slot words, or by `keywords` declared on a folder.
- **Renamed roots need an explicit `role`.** Root branch triggers match
  canonical roles (People, Financial, Legal, Property, Manuals, Misc). A
  renamed root declares `role: Financial` (etc.) so keyword routing finds
  it; root-level `keywords` add extra trigger words.
- **Interactive `setup` wizard.** `auto-file setup` prompts for inbox,
  destination root, and structure file (offering to generate a starter
  YAML from the built-in defaults); all three also accepted as flags for
  non-interactive use.
- **Personal files stay out of git.** `config.json`,
  `folder_structure*.yaml`, `*.db`, and `FOLDER_STRUCTURE.md` (contains
  personal names) are gitignored.

## YAML schema

```yaml
people: [Alpha, Bravo]            # person folder names (default: children of person_root)
person_subfolders: [Records, ...] # folders created per person
person_root: People               # which root holds per-person folders
roots:
  Money:
    role: Financial               # optional: canonical role of a renamed root
    keywords: [money]             # optional: extra words that trigger this root
    subfolders:
      Bank Statements: {}
      Purchases:
        keywords: [receipt]       # optional: extra words that pick this child
      Bills: {subfolders: [Receipts, Due]}
  Misc: {}
```

Matching rules:

- Folder selection tries declared `keywords` first where a branch targets
  a specific child (e.g. bank-statement branch looks for a child matching
  "bank statement" by name or keywords).
- Fallback order inside a root: keyword-matched child → Misc/General child
  → the root itself. Person routing: `person_subfolders` match →
  person-root child match → Misc person folder → the person folder.
- Unknown content falls back to the root named Misc (or the last root).

## Watcher loop guard (directional)

The inbox may legitimately live inside the destination root (Cabinet/Inbox
with dest=Cabinet). The old guard ignored anything under `target_root`,
which silently swallowed every inbox file in that layout. The guard is now
directional (`FolderWatcher._in_sorted_area`):

- destination inside inbox → ignore everything under the destination;
- inbox inside destination → ignore destination areas outside the inbox.

Regression-tested both layouts.

## Personal deployment (Kirby)

- Config: `~/.config/auto-file/config.json` — inbox
  `/mnt/ssd/drive-cabinet/Inbox`, dest `/mnt/ssd/drive-cabinet`, structure
  `~/.config/auto-file/folder_structure.yaml`.
- The structure YAML was generated from the live cabinet tree (7 roots,
  5 people, real subfolders incl. misspelled `Reciepts`; Banking/Taxes/
  Insurance carry keywords).
- Watcher runs as systemd user unit `auto-file-watch.service` (enabled).
