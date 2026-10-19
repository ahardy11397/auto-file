# Graph Report - auto-file  (2026-10-18)

## Corpus Check
- 40 files · ~30,824 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 711 nodes · 1687 edges · 26 communities (19 shown, 7 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 315 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3264e0f4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .rollback_run
- ExtractedContent
- detect_file_metadata
- resolve_target_filename
- TaxonomyRouter
- FolderWatcher
- Six-Stage Processing Pipeline
- test_cli.py
- CLI Interface (typer/rich)
- test_router.py
- auto_file
- cli.py
- FilePipelineExecutor
- test_understander.py
- executor.py
- _load_transformer_model
- UnderstandingResult
- AuditLedger
- RollbackError
- Path
- load_taxonomy
- _create_onnx_session
- _MockNdarray
- ._predict_onnx
- auto-file

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 58 edges
2. `FilePipelineExecutor` - 43 edges
3. `TaxonomyRouter` - 41 edges
4. `ExtractedContent` - 40 edges
5. `detect_file_metadata()` - 33 edges
6. `FileMetadata` - 31 edges
7. `FolderWatcher` - 29 edges
8. `GemmaUnderstander` - 28 edges
9. `get_extractor_for_tool()` - 22 edges
10. `LayaDispatcher` - 21 edges

## Surprising Connections (you probably didn't know these)
- `test_detect_text_file()` --uses--> `FileMetadata`  [INFERRED]
  tests/test_detector.py → src/auto_file/core/detector.py
- `_make_metadata()` --uses--> `FileMetadata`  [INFERRED]
  tests/test_router.py → src/auto_file/core/detector.py
- `test_cli_sort_failure_displays_dash_in_table()` --uses--> `PipelineResult`  [INFERRED]
  tests/test_cli.py → src/auto_file/core/executor.py
- `test_pipeline_dry_run_does_not_move_file()` --uses--> `PipelineResult`  [INFERRED]
  tests/test_executor.py → src/auto_file/core/executor.py
- `test_pipeline_live_move()` --uses--> `PipelineResult`  [INFERRED]
  tests/test_executor.py → src/auto_file/core/executor.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Laya Used Twice: Dispatch + Route** — idea_laya_decision_model, docs_superpowers_specs_2026_10_09_auto_file_system_design_dispatch_stage, docs_superpowers_specs_2026_10_09_auto_file_system_design_route_stage [EXTRACTED 1.00]
- **Reversibility Guarantee (hash + ledger + undo)** — docs_superpowers_specs_2026_10_09_auto_file_system_design_sqlite_audit_ledger, docs_superpowers_plans_2026_10_12_auto_file_system_rollback_safety, docs_superpowers_specs_2026_10_09_auto_file_system_design_execute_audit_stage [EXTRACTED 1.00]

## Communities (26 total, 7 thin omitted)

### Community 0 - ".rollback_run"
Cohesion: 0.14
Nodes (13): _sha256(), test_audit_lifecycle_and_rollback(), test_context_manager_support(), test_finish_run_and_get_history(), test_finish_run_auto_aggregates_counts(), test_rollback_collision_raises_strict(), test_rollback_collision_skips_when_not_strict(), test_rollback_hash_mismatch_raises_strict() (+5 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.12
Nodes (9): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor (+1 more)

### Community 2 - "detect_file_metadata"
Cohesion: 0.13
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 3 - "resolve_target_filename"
Cohesion: 0.09
Nodes (15): compute_file_sha256(), resolve_target_filename(), test_compute_file_sha256(), test_resolve_case_insensitive_collision(), test_resolve_collision_different_hash(), test_resolve_collision_identical_hash(), test_resolve_destination_dir_does_not_exist(), test_resolve_duplicate_found_at_numbered_suffix() (+7 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.13
Nodes (17): TaxonomyRouter, test_route_all_people(), test_route_exact_structure_spelling(), test_route_financial_bank_statement(), test_route_financial_bills(), test_route_financial_documents_by_entity(), test_route_financial_misc(), test_route_financial_receipts_by_entity() (+9 more)

### Community 5 - "FolderWatcher"
Cohesion: 0.05
Nodes (18): PipelineResult, FolderWatcher, _InboxEventHandler, test_pipeline_result_dataclass_coercion(), test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest() (+10 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.15
Nodes (13): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+5 more)

### Community 7 - "test_cli.py"
Cohesion: 0.07
Nodes (16): test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_no_args(), test_cli_sort_directory(), test_cli_sort_failure_displays_dash_in_table(), test_cli_sort_missing_dest_errors() (+8 more)

### Community 9 - "test_router.py"
Cohesion: 0.20
Nodes (11): LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension(), test_dispatch_standalone_function(), test_dispatch_text_files() (+3 more)

### Community 12 - "cli.py"
Cohesion: 0.06
Nodes (30): config(), history(), main(), _resolved_structure(), setup(), sort(), undo(), watch() (+22 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.08
Nodes (16): FilePipelineExecutor, test_pipeline_audit_rollback_restores_files(), test_pipeline_batch_process_directory(), test_pipeline_batch_process_directory_recursive(), test_pipeline_collision_different_content(), test_pipeline_date_precedence_content_date(), test_pipeline_date_precedence_exif_date(), test_pipeline_date_precedence_filesystem_fallback() (+8 more)

### Community 14 - "test_understander.py"
Cohesion: 0.06
Nodes (19): GemmaUnderstander, test_parse_conversational_wrapped_json(), test_parse_date_normalization_formats(), test_parse_entities_normalization(), test_parse_json_with_trailing_commas(), test_parse_llm_json_response_with_comments_before_brace_in_code_fence(), test_parse_raw_json_without_fences(), test_understander_custom_mock_response() (+11 more)

### Community 15 - "executor.py"
Cohesion: 0.10
Nodes (11): dispatch_tool(), ResolvedDestination, sanitize_slug(), resolve_destination(), route_destination(), _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text() (+3 more)

### Community 16 - "_load_transformer_model"
Cohesion: 0.14
Nodes (4): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only(), test_understanding_result_to_dict()

### Community 17 - "UnderstandingResult"
Cohesion: 0.15
Nodes (7): understand_content(), UnderstandingResult, test_parse_empty_and_garbage_input_safety(), test_parse_malformed_json_fallback(), test_parse_valid_json_response(), test_understander_callable_interface(), test_understander_standalone_function()

### Community 18 - "AuditLedger"
Cohesion: 0.10
Nodes (6): AuditLedger, test_empty_database_rollback(), test_cli_history_with_run_id(), test_cli_live_sort_single_file(), test_cli_undo_by_run_id(), test_pipeline_batch_process_directory_dry_run()

### Community 19 - "RollbackError"
Cohesion: 0.19
Nodes (5): AuditError, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError

### Community 21 - "load_taxonomy"
Cohesion: 0.09
Nodes (8): child_key(), load_taxonomy(), _matches(), _norm(), _parse_folder_spec(), Taxonomy, test_load_taxonomy_missing_file(), test_load_taxonomy_missing_roots()

### Community 25 - "auto-file"
Cohesion: 0.17
Nodes (11): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, Naming (+3 more)

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 311 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditLedger` connect `AuditLedger` to `.rollback_run`, `FolderWatcher`, `test_cli.py`, `cli.py`, `FilePipelineExecutor`, `executor.py`, `RollbackError`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 41 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.rollback_run` be split into smaller, more focused modules?**
  _Cohesion score 0.1411764705882353 - nodes in this community are weakly interconnected._
- **Why does `TaxonomyRouter` connect `TaxonomyRouter` to `FilePipelineExecutor`, `executor.py`, `Path`, `load_taxonomy`, `_create_onnx_session`, `_MockNdarray`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `FilePipelineExecutor` (e.g. with `sort()` and `watch()`) actually correct?**
  _`FilePipelineExecutor` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.11616161616161616 - nodes in this community are weakly interconnected._