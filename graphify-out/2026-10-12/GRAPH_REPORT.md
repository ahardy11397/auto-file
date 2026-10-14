# Graph Report - auto-file  (2026-10-12)

## Corpus Check
- Corpus is ~11,960 words - fits in a single context window. You may not need a graph.

## Summary
- 265 nodes · 573 edges · 12 communities (7 shown, 5 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 77 edges (avg confidence: 0.89)
- Token cost: 4,254 input · 2,800 output

## Community Hubs (Navigation)
- Audit Ledger & Undo
- Content Extractors
- Detection & Extractor Tests
- Naming & Collision Resolution
- Laya Dispatcher & Router
- Audit Exceptions
- Design Docs & Concepts
- CLI & Watcher Spec
- Installed Package

## God Nodes (most connected - your core abstractions)
1. `detect_file_metadata()` - 30 edges
2. `AuditLedger` - 27 edges
3. `FileMetadata` - 22 edges
4. `get_extractor_for_tool()` - 20 edges
5. `ExtractedContent` - 19 edges
6. `BaseExtractor` - 17 edges
7. `resolve_target_filename()` - 15 edges
8. `test_rollback_hash_mismatch_raises_strict()` - 11 edges
9. `test_rollback_collision_raises_strict()` - 11 edges
10. `_sha256()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `test_detect_text_file()` --uses--> `FileMetadata`  [INFERRED]
  tests/test_detector.py → src/auto_file/core/detector.py
- `_make_metadata()` --uses--> `FileMetadata`  [INFERRED]
  tests/test_router.py → src/auto_file/core/detector.py
- `test_rollback_hash_mismatch_raises_strict()` --uses--> `RollbackVerificationError`  [INFERRED]
  tests/test_audit.py → src/auto_file/storage/audit.py
- `test_rollback_missing_destination_file()` --uses--> `RollbackMissingFileError`  [INFERRED]
  tests/test_audit.py → src/auto_file/storage/audit.py
- `test_rollback_collision_raises_strict()` --uses--> `RollbackCollisionError`  [INFERRED]
  tests/test_audit.py → src/auto_file/storage/audit.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Laya Used Twice: Dispatch + Route** — idea_laya_decision_model, docs_superpowers_specs_2026_10_09_auto_file_system_design_dispatch_stage, docs_superpowers_specs_2026_10_09_auto_file_system_design_route_stage [EXTRACTED 1.00]
- **Reversibility Guarantee (hash + ledger + undo)** — docs_superpowers_specs_2026_10_09_auto_file_system_design_sqlite_audit_ledger, docs_superpowers_plans_2026_10_12_auto_file_system_rollback_safety, docs_superpowers_specs_2026_10_09_auto_file_system_design_execute_audit_stage [EXTRACTED 1.00]

## Communities (12 total, 5 thin omitted)

### Community 0 - "Audit Ledger & Undo"
Cohesion: 0.09
Nodes (15): AuditLedger, _sha256(), test_audit_lifecycle_and_rollback(), test_context_manager_support(), test_empty_database_rollback(), test_finish_run_and_get_history(), test_finish_run_auto_aggregates_counts(), test_rollback_collision_raises_strict() (+7 more)

### Community 1 - "Content Extractors"
Cohesion: 0.11
Nodes (9): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor (+1 more)

### Community 2 - "Detection & Extractor Tests"
Cohesion: 0.13
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 3 - "Naming & Collision Resolution"
Cohesion: 0.09
Nodes (15): compute_file_sha256(), resolve_target_filename(), ResolvedDestination, sanitize_slug(), test_compute_file_sha256(), test_resolve_case_insensitive_collision(), test_resolve_collision_different_hash(), test_resolve_collision_identical_hash() (+7 more)

### Community 4 - "Laya Dispatcher & Router"
Cohesion: 0.08
Nodes (11): _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension(), test_dispatch_standalone_function(), test_dispatch_text_files(), test_dispatcher_onnx_fallback_on_error() (+3 more)

### Community 5 - "Audit Exceptions"
Cohesion: 0.14
Nodes (5): AuditError, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError

### Community 6 - "Design Docs & Concepts"
Cohesion: 0.15
Nodes (13): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+5 more)

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Graphify Project Rules`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Folder Watcher Daemon` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 114 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditLedger` connect `Audit Ledger & Undo` to `Audit Exceptions`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `AuditLedger` (e.g. with `test_audit_lifecycle_and_rollback()` and `test_context_manager_support()`) actually correct?**
  _`AuditLedger` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Graphify Project Rules`, `Detect Stage` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Audit Ledger & Undo` be split into smaller, more focused modules?**
  _Cohesion score 0.09154437456324249 - nodes in this community are weakly interconnected._
- **Why does `detect_file_metadata()` connect `Detection & Extractor Tests` to `Content Extractors`, `Naming & Collision Resolution`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `FileMetadata` (e.g. with `AudioExtractor` and `BaseExtractor`) actually correct?**
  _`FileMetadata` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `Content Extractors` be split into smaller, more focused modules?**
  _Cohesion score 0.11008325624421832 - nodes in this community are weakly interconnected._