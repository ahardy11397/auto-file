# Graph Report - auto-file  (2026-10-19)

## Corpus Check
- 40 files · ~32,741 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 746 nodes · 1763 edges · 33 communities (22 shown, 11 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 343 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0d96e7a9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .rollback_run
- FileMetadata
- detect_file_metadata
- resolve_target_filename
- TaxonomyRouter
- FolderWatcher
- Six-Stage Processing Pipeline
- test_cli.py
- CLI Interface (typer/rich)
- LayaDispatcher
- auto_file
- cli.py
- FilePipelineExecutor
- test_understander.py
- executor.py
- _load_transformer_model
- ExtractedContent
- AuditLedger
- audit.py
- test_watcher_boundary_checks_and_nested_target_root
- Taxonomy
- load_taxonomy
- default_taxonomy
- test_taxonomy.py
- auto-file
- ._match
- _InboxEventHandler
- Config-Driven Folder Structure — Design (2026-10-18)
- PipelineResult
- .extract
- child_key
- test_watcher_context_manager

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 60 edges
2. `TaxonomyRouter` - 49 edges
3. `FilePipelineExecutor` - 44 edges
4. `ExtractedContent` - 40 edges
5. `detect_file_metadata()` - 33 edges
6. `FileMetadata` - 31 edges
7. `FolderWatcher` - 31 edges
8. `GemmaUnderstander` - 28 edges
9. `load_taxonomy()` - 23 edges
10. `get_extractor_for_tool()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Running the watcher continuously` --references--> `sort()`  [INFERRED]
  README.md → src/auto_file/cli.py
- `Decisions` --references--> `sort()`  [INFERRED]
  docs/superpowers/specs/2026-10-18-config-driven-taxonomy-design.md → src/auto_file/cli.py
- `Decisions` --references--> `watch()`  [INFERRED]
  docs/superpowers/specs/2026-10-18-config-driven-taxonomy-design.md → src/auto_file/cli.py
- `Decisions` --references--> `setup()`  [INFERRED]
  docs/superpowers/specs/2026-10-18-config-driven-taxonomy-design.md → src/auto_file/cli.py
- `test_cli_sort_rejects_invalid_structure_file()` --calls--> `set_config_value()`  [EXTRACTED]
  tests/test_taxonomy.py → src/auto_file/config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Laya Used Twice: Dispatch + Route** — idea_laya_decision_model, docs_superpowers_specs_2026_10_09_auto_file_system_design_dispatch_stage, docs_superpowers_specs_2026_10_09_auto_file_system_design_route_stage [EXTRACTED 1.00]
- **Reversibility Guarantee (hash + ledger + undo)** — docs_superpowers_specs_2026_10_09_auto_file_system_design_sqlite_audit_ledger, docs_superpowers_plans_2026_10_12_auto_file_system_rollback_safety, docs_superpowers_specs_2026_10_09_auto_file_system_design_execute_audit_stage [EXTRACTED 1.00]

## Communities (33 total, 11 thin omitted)

### Community 0 - ".rollback_run"
Cohesion: 0.15
Nodes (12): _sha256(), test_audit_lifecycle_and_rollback(), test_context_manager_support(), test_finish_run_auto_aggregates_counts(), test_rollback_collision_raises_strict(), test_rollback_collision_skips_when_not_strict(), test_rollback_hash_mismatch_raises_strict(), test_rollback_hash_mismatch_skips_when_not_strict() (+4 more)

### Community 1 - "FileMetadata"
Cohesion: 0.16
Nodes (5): FileMetadata, AudioExtractor, BaseExtractor, PDFExtractor, TextExtractor

### Community 2 - "detect_file_metadata"
Cohesion: 0.17
Nodes (19): detect_file_metadata(), get_extractor_for_tool(), test_audio_extractor_no_tags(), test_audio_extractor_tags(), test_fallback_extractor(), test_get_extractor_registry(), test_image_extractor_basic(), test_image_extractor_corrupted_file() (+11 more)

### Community 3 - "resolve_target_filename"
Cohesion: 0.07
Nodes (22): compute_file_sha256(), resolve_target_filename(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+14 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.05
Nodes (27): _create_onnx_session(), resolve_destination(), route_destination(), sanitize_folder_name(), TaxonomyRouter, first_entity(), _MockNdarray, test_route_all_people() (+19 more)

### Community 5 - "FolderWatcher"
Cohesion: 0.11
Nodes (14): FolderWatcher, test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest(), test_watcher_debounce_waits_for_file_stability(), test_watcher_detects_and_sorts_file(), test_watcher_ignores_hidden_files() (+6 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.16
Nodes (11): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+3 more)

### Community 7 - "test_cli.py"
Cohesion: 0.07
Nodes (16): test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_no_args(), test_cli_sort_directory(), test_cli_sort_failure_displays_dash_in_table(), test_cli_sort_missing_dest_errors() (+8 more)

### Community 9 - "LayaDispatcher"
Cohesion: 0.11
Nodes (13): _create_onnx_session(), dispatch_tool(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension() (+5 more)

### Community 12 - "cli.py"
Cohesion: 0.08
Nodes (19): Decisions, config(), history(), main(), _resolved_structure(), setup(), sort(), undo() (+11 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.10
Nodes (17): FilePipelineExecutor, test_pipeline_audit_rollback_restores_files(), test_pipeline_batch_process_directory(), test_pipeline_batch_process_directory_dry_run(), test_pipeline_batch_process_directory_recursive(), test_pipeline_collision_different_content(), test_pipeline_date_precedence_content_date(), test_pipeline_date_precedence_exif_date() (+9 more)

### Community 14 - "test_understander.py"
Cohesion: 0.10
Nodes (14): GemmaUnderstander, test_understander_callable_interface(), test_understander_custom_mock_response(), test_understander_deterministic_audio_metadata(), test_understander_deterministic_image_with_exif(), test_understander_deterministic_markdown_header_slug(), test_understander_deterministic_medical_record(), test_understander_deterministic_text_bank_statement() (+6 more)

### Community 15 - "executor.py"
Cohesion: 0.05
Nodes (20): ResolvedDestination, sanitize_slug(), _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text(), normalize_date_string(), parse_llm_json_response() (+12 more)

### Community 16 - "_load_transformer_model"
Cohesion: 0.22
Nodes (3): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only()

### Community 17 - "ExtractedContent"
Cohesion: 0.20
Nodes (4): ExtractedContent, FallbackExtractor, ImageExtractor, test_understander_standalone_function()

### Community 18 - "AuditLedger"
Cohesion: 0.09
Nodes (6): AuditLedger, test_empty_database_rollback(), test_finish_run_and_get_history(), test_cli_history_with_run_id(), test_cli_live_sort_single_file(), test_cli_undo_by_run_id()

### Community 19 - "audit.py"
Cohesion: 0.15
Nodes (5): AuditError, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError

### Community 22 - "load_taxonomy"
Cohesion: 0.22
Nodes (6): load_taxonomy(), test_load_taxonomy_missing_file(), test_load_taxonomy_missing_roots(), test_router_insurance_letter_routes_to_insurance_child(), test_router_root_keywords_route_traffic(), test_router_scanned_document_files_by_filename()

### Community 23 - "default_taxonomy"
Cohesion: 0.25
Nodes (6): default_taxonomy(), taxonomy_to_yaml(), test_cli_setup_noninteractive_generates_structure(), test_default_taxonomy_exact_spelling(), test_default_taxonomy_matches_builtin_constants(), test_taxonomy_to_yaml_round_trip()

### Community 24 - "test_taxonomy.py"
Cohesion: 0.15
Nodes (10): test_cli_sort_rejects_invalid_structure_file(), test_cli_sort_uses_configured_structure(), test_executor_loads_structure_file(), test_heuristic_hint_insurance_letter(), test_heuristic_medical_requires_specific_terms(), test_heuristic_resume_outranks_medical(), test_load_taxonomy_custom_yaml(), test_resolve_destination_structure_argument() (+2 more)

### Community 25 - "auto-file"
Cohesion: 0.15
Nodes (12): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, Naming (+4 more)

### Community 28 - "Config-Driven Folder Structure — Design (2026-10-18)"
Cohesion: 0.33
Nodes (5): Config-Driven Folder Structure — Design (2026-10-18), Intent, Personal deployment (Kirby), Watcher loop guard (directional), YAML schema

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 327 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditLedger` connect `AuditLedger` to `.rollback_run`, `test_watcher_context_manager`, `FolderWatcher`, `test_cli.py`, `LayaDispatcher`, `cli.py`, `FilePipelineExecutor`, `executor.py`, `audit.py`, `test_watcher_boundary_checks_and_nested_target_root`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Are the 42 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 42 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `resolve_target_filename` be split into smaller, more focused modules?**
  _Cohesion score 0.07439613526570048 - nodes in this community are weakly interconnected._
- **Why does `TaxonomyRouter` connect `TaxonomyRouter` to `LayaDispatcher`, `FilePipelineExecutor`, `executor.py`, `Taxonomy`, `load_taxonomy`, `test_taxonomy.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `TaxonomyRouter` (e.g. with `FilePipelineExecutor` and `Taxonomy`) actually correct?**
  _`TaxonomyRouter` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `TaxonomyRouter` be split into smaller, more focused modules?**
  _Cohesion score 0.05017543859649123 - nodes in this community are weakly interconnected._