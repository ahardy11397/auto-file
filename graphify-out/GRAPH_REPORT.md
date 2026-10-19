# Graph Report - auto-file  (2026-10-18)

## Corpus Check
- 40 files · ~31,744 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 727 nodes · 1722 edges · 32 communities (21 shown, 11 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 327 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4af1d9f2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .rollback_run
- ExtractedContent
- detect_file_metadata
- resolve_target_filename
- TaxonomyRouter
- test_watcher.py
- Six-Stage Processing Pipeline
- test_cli.py
- CLI Interface (typer/rich)
- LayaDispatcher
- auto_file
- cli.py
- FilePipelineExecutor
- GemmaUnderstander
- core/__init__.py
- _load_transformer_model
- UnderstandingResult
- AuditLedger
- audit.py
- Path
- executor.py
- _create_onnx_session
- _MockNdarray
- test_watcher_boundary_checks_and_nested_target_root
- auto-file
- PipelineResult
- _InboxEventHandler
- test_watcher_context_manager
- FolderWatcher
- test_understander.py
- Any

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 59 edges
2. `FilePipelineExecutor` - 44 edges
3. `TaxonomyRouter` - 43 edges
4. `ExtractedContent` - 40 edges
5. `detect_file_metadata()` - 33 edges
6. `FileMetadata` - 31 edges
7. `FolderWatcher` - 31 edges
8. `GemmaUnderstander` - 28 edges
9. `get_extractor_for_tool()` - 22 edges
10. `LayaDispatcher` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Running the watcher continuously` --references--> `sort()`  [INFERRED]
  README.md → src/auto_file/cli.py
- `Decisions` --references--> `sort()`  [INFERRED]
  docs/superpowers/specs/2026-10-18-config-driven-taxonomy-design.md → src/auto_file/cli.py
- `Decisions` --references--> `watch()`  [INFERRED]
  docs/superpowers/specs/2026-10-18-config-driven-taxonomy-design.md → src/auto_file/cli.py
- `Decisions` --references--> `setup()`  [INFERRED]
  docs/superpowers/specs/2026-10-18-config-driven-taxonomy-design.md → src/auto_file/cli.py
- `test_detect_text_file()` --uses--> `FileMetadata`  [INFERRED]
  tests/test_detector.py → src/auto_file/core/detector.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Laya Used Twice: Dispatch + Route** — idea_laya_decision_model, docs_superpowers_specs_2026_10_09_auto_file_system_design_dispatch_stage, docs_superpowers_specs_2026_10_09_auto_file_system_design_route_stage [EXTRACTED 1.00]
- **Reversibility Guarantee (hash + ledger + undo)** — docs_superpowers_specs_2026_10_09_auto_file_system_design_sqlite_audit_ledger, docs_superpowers_plans_2026_10_12_auto_file_system_rollback_safety, docs_superpowers_specs_2026_10_09_auto_file_system_design_execute_audit_stage [EXTRACTED 1.00]

## Communities (32 total, 11 thin omitted)

### Community 0 - ".rollback_run"
Cohesion: 0.13
Nodes (14): _sha256(), test_audit_lifecycle_and_rollback(), test_context_manager_support(), test_empty_database_rollback(), test_finish_run_and_get_history(), test_finish_run_auto_aggregates_counts(), test_rollback_collision_raises_strict(), test_rollback_collision_skips_when_not_strict() (+6 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.11
Nodes (9): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor (+1 more)

### Community 2 - "detect_file_metadata"
Cohesion: 0.17
Nodes (19): detect_file_metadata(), get_extractor_for_tool(), test_audio_extractor_no_tags(), test_audio_extractor_tags(), test_fallback_extractor(), test_get_extractor_registry(), test_image_extractor_basic(), test_image_extractor_corrupted_file() (+11 more)

### Community 3 - "resolve_target_filename"
Cohesion: 0.07
Nodes (22): compute_file_sha256(), resolve_target_filename(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+14 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.13
Nodes (17): TaxonomyRouter, test_route_all_people(), test_route_exact_structure_spelling(), test_route_financial_bank_statement(), test_route_financial_bills(), test_route_financial_documents_by_entity(), test_route_financial_misc(), test_route_financial_receipts_by_entity() (+9 more)

### Community 5 - "test_watcher.py"
Cohesion: 0.14
Nodes (9): test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest(), test_watcher_detects_and_sorts_file(), test_watcher_ignores_hidden_files(), test_watcher_non_recursive_mode_ignores_subdirectories(), test_watcher_on_processed_callback() (+1 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.16
Nodes (11): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+3 more)

### Community 7 - "test_cli.py"
Cohesion: 0.06
Nodes (15): test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_no_args(), test_cli_sort_directory(), test_cli_sort_failure_displays_dash_in_table(), test_cli_sort_missing_dest_errors() (+7 more)

### Community 9 - "LayaDispatcher"
Cohesion: 0.12
Nodes (13): _create_onnx_session(), dispatch_tool(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension() (+5 more)

### Community 12 - "cli.py"
Cohesion: 0.06
Nodes (26): Config-Driven Folder Structure — Design (2026-10-18), Decisions, Intent, Personal deployment (Kirby), Watcher loop guard (directional), YAML schema, Running the watcher continuously, config() (+18 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.10
Nodes (17): FilePipelineExecutor, test_pipeline_audit_rollback_restores_files(), test_pipeline_batch_process_directory(), test_pipeline_batch_process_directory_dry_run(), test_pipeline_batch_process_directory_recursive(), test_pipeline_collision_different_content(), test_pipeline_date_precedence_content_date(), test_pipeline_date_precedence_exif_date() (+9 more)

### Community 14 - "GemmaUnderstander"
Cohesion: 0.10
Nodes (12): GemmaUnderstander, test_understander_custom_mock_response(), test_understander_deterministic_audio_metadata(), test_understander_deterministic_image_with_exif(), test_understander_deterministic_markdown_header_slug(), test_understander_deterministic_medical_record(), test_understander_deterministic_text_bank_statement(), test_understander_image_without_exif() (+4 more)

### Community 15 - "core/__init__.py"
Cohesion: 0.15
Nodes (8): ResolvedDestination, sanitize_slug(), _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text(), normalize_date_string(), parse_llm_json_response()

### Community 16 - "_load_transformer_model"
Cohesion: 0.22
Nodes (3): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only()

### Community 17 - "UnderstandingResult"
Cohesion: 0.15
Nodes (7): understand_content(), UnderstandingResult, test_parse_empty_and_garbage_input_safety(), test_parse_malformed_json_fallback(), test_parse_valid_json_response(), test_understander_callable_interface(), test_understander_standalone_function()

### Community 18 - "AuditLedger"
Cohesion: 0.10
Nodes (5): AuditLedger, test_cli_history_with_run_id(), test_cli_live_sort_single_file(), test_cli_undo_by_run_id(), test_cli_undo_no_files_to_undo()

### Community 19 - "audit.py"
Cohesion: 0.15
Nodes (5): AuditError, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError

### Community 21 - "executor.py"
Cohesion: 0.05
Nodes (23): resolve_destination(), route_destination(), child_key(), default_taxonomy(), load_taxonomy(), _matches(), _norm(), _parse_folder_spec() (+15 more)

### Community 25 - "auto-file"
Cohesion: 0.17
Nodes (11): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, Naming (+3 more)

### Community 29 - "FolderWatcher"
Cohesion: 0.21
Nodes (5): FolderWatcher, test_watcher_debounce_waits_for_file_stability(), test_watcher_ignores_temporary_extensions(), test_watcher_processes_renamed_temp_file(), test_watcher_recursive_mode()

### Community 30 - "test_understander.py"
Cohesion: 0.12
Nodes (7): test_parse_conversational_wrapped_json(), test_parse_date_normalization_formats(), test_parse_entities_normalization(), test_parse_json_with_trailing_commas(), test_parse_llm_json_response_with_comments_before_brace_in_code_fence(), test_parse_raw_json_without_fences(), test_understander_lazy_initialization()

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 319 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditLedger` connect `AuditLedger` to `.rollback_run`, `test_watcher.py`, `cli.py`, `FilePipelineExecutor`, `audit.py`, `executor.py`, `test_watcher_boundary_checks_and_nested_target_root`, `test_watcher_context_manager`, `FolderWatcher`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Are the 42 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 42 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.rollback_run` be split into smaller, more focused modules?**
  _Cohesion score 0.13213213213213212 - nodes in this community are weakly interconnected._
- **Why does `FilePipelineExecutor` connect `FilePipelineExecutor` to `TaxonomyRouter`, `test_watcher.py`, `LayaDispatcher`, `cli.py`, `GemmaUnderstander`, `core/__init__.py`, `AuditLedger`, `executor.py`, `test_watcher_boundary_checks_and_nested_target_root`, `PipelineResult`, `test_watcher_context_manager`, `FolderWatcher`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `FilePipelineExecutor` (e.g. with `sort()` and `watch()`) actually correct?**
  _`FilePipelineExecutor` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.11304347826086956 - nodes in this community are weakly interconnected._