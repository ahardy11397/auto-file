# Graph Report - auto-file  (2026-10-19)

## Corpus Check
- 41 files · ~34,409 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 776 nodes · 1833 edges · 40 communities (23 shown, 17 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 365 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8727dba6`
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
- .understand
- understander.py
- _load_transformer_model
- test_watcher_boundary_checks_and_nested_target_root
- AuditLedger
- audit.py
- Path
- Taxonomy
- GemmaUnderstander
- default_taxonomy
- test_taxonomy.py
- auto-file
- conftest.py
- _InboxEventHandler
- _create_onnx_session
- _MockNdarray
- test_router_no_false_person_from_partial_name
- test_understander.py
- executor.py
- FolderWatcher
- PipelineResult
- Any
- _FakeResponse
- test_watcher_context_manager
- test_understander_deterministic_medical_record
- test_understander_deterministic_markdown_header_slug

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 61 edges
2. `TaxonomyRouter` - 49 edges
3. `FilePipelineExecutor` - 47 edges
4. `ExtractedContent` - 42 edges
5. `GemmaUnderstander` - 35 edges
6. `detect_file_metadata()` - 33 edges
7. `FileMetadata` - 31 edges
8. `FolderWatcher` - 31 edges
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

## Communities (40 total, 17 thin omitted)

### Community 0 - ".rollback_run"
Cohesion: 0.15
Nodes (12): _sha256(), test_audit_lifecycle_and_rollback(), test_context_manager_support(), test_empty_database_rollback(), test_rollback_collision_raises_strict(), test_rollback_collision_skips_when_not_strict(), test_rollback_hash_mismatch_raises_strict(), test_rollback_hash_mismatch_skips_when_not_strict() (+4 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.12
Nodes (9): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor (+1 more)

### Community 2 - "detect_file_metadata"
Cohesion: 0.12
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 3 - "resolve_target_filename"
Cohesion: 0.09
Nodes (16): compute_file_sha256(), resolve_target_filename(), ResolvedDestination, test_compute_file_sha256(), test_resolve_case_insensitive_collision(), test_resolve_collision_different_hash(), test_resolve_collision_identical_hash(), test_resolve_destination_dir_does_not_exist() (+8 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.12
Nodes (20): TaxonomyRouter, test_route_all_people(), test_route_exact_structure_spelling(), test_route_financial_bank_statement(), test_route_financial_bills(), test_route_financial_documents_by_entity(), test_route_financial_misc(), test_route_financial_receipts_by_entity() (+12 more)

### Community 5 - "test_watcher.py"
Cohesion: 0.14
Nodes (9): test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest(), test_watcher_detects_and_sorts_file(), test_watcher_ignores_hidden_files(), test_watcher_non_recursive_mode_ignores_subdirectories(), test_watcher_on_processed_callback() (+1 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.16
Nodes (11): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+3 more)

### Community 7 - "test_cli.py"
Cohesion: 0.07
Nodes (16): test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_no_args(), test_cli_sort_directory(), test_cli_sort_failure_displays_dash_in_table(), test_cli_sort_missing_dest_errors() (+8 more)

### Community 9 - "LayaDispatcher"
Cohesion: 0.12
Nodes (13): _create_onnx_session(), dispatch_tool(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension() (+5 more)

### Community 12 - "cli.py"
Cohesion: 0.07
Nodes (24): Config-Driven Folder Structure — Design (2026-10-18), Decisions, Intent, Personal deployment (Kirby), Watcher loop guard (directional), YAML schema, config(), history() (+16 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.10
Nodes (20): FilePipelineExecutor, test_pipeline_audit_rollback_restores_files(), test_pipeline_batch_process_directory(), test_pipeline_batch_process_directory_dry_run(), test_pipeline_batch_process_directory_recursive(), test_pipeline_collision_different_content(), test_pipeline_date_precedence_content_date(), test_pipeline_date_precedence_exif_date() (+12 more)

### Community 14 - ".understand"
Cohesion: 0.12
Nodes (7): test_understander_custom_mock_response(), test_understander_deterministic_audio_metadata(), test_understander_deterministic_image_with_exif(), test_understander_deterministic_text_bank_statement(), test_understander_image_without_exif(), test_understander_neural_inference_exception_fallback(), test_understander_neural_inference_mocked()

### Community 15 - "understander.py"
Cohesion: 0.12
Nodes (13): sanitize_slug(), _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text(), normalize_date_string(), parse_llm_json_response(), understand_content() (+5 more)

### Community 16 - "_load_transformer_model"
Cohesion: 0.22
Nodes (3): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only()

### Community 18 - "AuditLedger"
Cohesion: 0.10
Nodes (6): AuditLedger, test_finish_run_and_get_history(), test_finish_run_auto_aggregates_counts(), test_cli_history_with_run_id(), test_cli_live_sort_single_file(), test_cli_undo_by_run_id()

### Community 19 - "audit.py"
Cohesion: 0.16
Nodes (5): AuditError, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError

### Community 21 - "Taxonomy"
Cohesion: 0.10
Nodes (5): child_key(), _matches(), _norm(), _parse_folder_spec(), Taxonomy

### Community 22 - "GemmaUnderstander"
Cohesion: 0.15
Nodes (5): GemmaUnderstander, test_understander_callable_interface(), test_understander_lazy_initialization(), test_understander_long_text_truncation_in_prompt(), test_understander_prompt_generation()

### Community 23 - "default_taxonomy"
Cohesion: 0.20
Nodes (6): default_taxonomy(), taxonomy_to_yaml(), test_cli_setup_noninteractive_generates_structure(), test_default_taxonomy_exact_spelling(), test_default_taxonomy_matches_builtin_constants(), test_taxonomy_to_yaml_round_trip()

### Community 24 - "test_taxonomy.py"
Cohesion: 0.10
Nodes (16): load_taxonomy(), test_cli_sort_rejects_invalid_structure_file(), test_cli_sort_uses_configured_structure(), test_executor_loads_structure_file(), test_heuristic_hint_insurance_letter(), test_heuristic_medical_requires_specific_terms(), test_heuristic_resume_outranks_medical(), test_load_taxonomy_custom_yaml() (+8 more)

### Community 25 - "auto-file"
Cohesion: 0.15
Nodes (12): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, Naming (+4 more)

### Community 31 - "test_understander.py"
Cohesion: 0.10
Nodes (12): _content(), test_deterministic_rich_generic_text_is_understood(), test_deterministic_scan_without_text_is_not_understood(), test_deterministic_specific_category_is_understood(), test_llama_server_unreachable_falls_back_to_deterministic(), test_neural_empty_output_is_not_understood(), test_parse_conversational_wrapped_json(), test_parse_date_normalization_formats() (+4 more)

### Community 33 - "FolderWatcher"
Cohesion: 0.21
Nodes (5): FolderWatcher, test_watcher_debounce_waits_for_file_stability(), test_watcher_ignores_temporary_extensions(), test_watcher_processes_renamed_temp_file(), test_watcher_recursive_mode()

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 342 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FilePipelineExecutor` connect `FilePipelineExecutor` to `executor.py`, `FolderWatcher`, `PipelineResult`, `TaxonomyRouter`, `test_watcher_context_manager`, `test_watcher.py`, `LayaDispatcher`, `cli.py`, `understander.py`, `test_watcher_boundary_checks_and_nested_target_root`, `AuditLedger`, `GemmaUnderstander`, `test_taxonomy.py`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 43 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.rollback_run` be split into smaller, more focused modules?**
  _Cohesion score 0.14962121212121213 - nodes in this community are weakly interconnected._
- **Why does `TaxonomyRouter` connect `TaxonomyRouter` to `executor.py`, `FilePipelineExecutor`, `understander.py`, `Path`, `Taxonomy`, `default_taxonomy`, `test_taxonomy.py`, `_create_onnx_session`, `test_router_no_false_person_from_partial_name`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `TaxonomyRouter` (e.g. with `FilePipelineExecutor` and `Taxonomy`) actually correct?**
  _`TaxonomyRouter` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.11616161616161616 - nodes in this community are weakly interconnected._