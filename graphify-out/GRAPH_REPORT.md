# Graph Report - auto-file  (2026-10-19)

## Corpus Check
- 41 files · ~33,758 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 764 nodes · 1806 edges · 32 communities (21 shown, 11 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 360 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a56a29a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .rollback_run
- FileMetadata
- detect_file_metadata
- executor.py
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
- understander.py
- _load_transformer_model
- UnderstandingResult
- AuditLedger
- RollbackError
- Path
- Taxonomy
- ExtractedContent
- default_taxonomy
- test_taxonomy.py
- auto-file
- conftest.py
- _InboxEventHandler
- _create_onnx_session
- _MockNdarray
- test_router_no_false_person_from_partial_name
- test_parse_llm_json_response_with_comments_before_brace_in_code_fence

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 61 edges
2. `TaxonomyRouter` - 49 edges
3. `FilePipelineExecutor` - 47 edges
4. `ExtractedContent` - 41 edges
5. `detect_file_metadata()` - 33 edges
6. `GemmaUnderstander` - 32 edges
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

## Communities (32 total, 11 thin omitted)

### Community 0 - ".rollback_run"
Cohesion: 0.13
Nodes (14): _sha256(), test_audit_lifecycle_and_rollback(), test_context_manager_support(), test_empty_database_rollback(), test_finish_run_and_get_history(), test_finish_run_auto_aggregates_counts(), test_rollback_collision_raises_strict(), test_rollback_collision_skips_when_not_strict() (+6 more)

### Community 1 - "FileMetadata"
Cohesion: 0.11
Nodes (8): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, FallbackExtractor, ImageExtractor, PDFExtractor, TextExtractor

### Community 2 - "detect_file_metadata"
Cohesion: 0.12
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 3 - "executor.py"
Cohesion: 0.05
Nodes (19): compute_file_sha256(), resolve_target_filename(), ResolvedDestination, sanitize_slug(), resolve_destination(), route_destination(), test_compute_file_sha256(), test_resolve_case_insensitive_collision() (+11 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.12
Nodes (19): TaxonomyRouter, test_route_all_people(), test_route_exact_structure_spelling(), test_route_financial_bank_statement(), test_route_financial_bills(), test_route_financial_documents_by_entity(), test_route_financial_misc(), test_route_financial_receipts_by_entity() (+11 more)

### Community 5 - "FolderWatcher"
Cohesion: 0.07
Nodes (18): PipelineResult, FolderWatcher, test_pipeline_result_dataclass_coercion(), test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest(), test_watcher_boundary_checks_and_nested_target_root() (+10 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.16
Nodes (11): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+3 more)

### Community 7 - "test_cli.py"
Cohesion: 0.06
Nodes (19): test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_history_with_run_id(), test_cli_live_sort_single_file(), test_cli_no_args(), test_cli_sort_directory() (+11 more)

### Community 9 - "LayaDispatcher"
Cohesion: 0.12
Nodes (13): _create_onnx_session(), dispatch_tool(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension() (+5 more)

### Community 12 - "cli.py"
Cohesion: 0.07
Nodes (24): Config-Driven Folder Structure — Design (2026-10-18), Decisions, Intent, Personal deployment (Kirby), Watcher loop guard (directional), YAML schema, config(), history() (+16 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.09
Nodes (19): FilePipelineExecutor, test_pipeline_audit_rollback_restores_files(), test_pipeline_batch_process_directory(), test_pipeline_batch_process_directory_dry_run(), test_pipeline_batch_process_directory_recursive(), test_pipeline_collision_different_content(), test_pipeline_date_precedence_content_date(), test_pipeline_date_precedence_filesystem_fallback() (+11 more)

### Community 14 - "test_understander.py"
Cohesion: 0.11
Nodes (16): GemmaUnderstander, _content(), test_deterministic_rich_generic_text_is_understood(), test_deterministic_scan_without_text_is_not_understood(), test_deterministic_specific_category_is_understood(), test_neural_empty_output_is_not_understood(), test_understander_custom_mock_response(), test_understander_deterministic_audio_metadata() (+8 more)

### Community 15 - "understander.py"
Cohesion: 0.11
Nodes (11): _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text(), normalize_date_string(), parse_llm_json_response(), test_parse_conversational_wrapped_json(), test_parse_date_normalization_formats() (+3 more)

### Community 16 - "_load_transformer_model"
Cohesion: 0.12
Nodes (4): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only(), test_understanding_result_to_dict()

### Community 17 - "UnderstandingResult"
Cohesion: 0.13
Nodes (8): understand_content(), UnderstandingResult, test_pipeline_date_precedence_exif_date(), test_parse_empty_and_garbage_input_safety(), test_parse_malformed_json_fallback(), test_parse_valid_json_response(), test_understander_callable_interface(), test_understander_standalone_function()

### Community 19 - "RollbackError"
Cohesion: 0.19
Nodes (5): AuditError, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError

### Community 21 - "Taxonomy"
Cohesion: 0.10
Nodes (5): child_key(), _matches(), _norm(), _parse_folder_spec(), Taxonomy

### Community 22 - "ExtractedContent"
Cohesion: 0.24
Nodes (3): ExtractedContent, test_understander_long_text_truncation_in_prompt(), test_understander_prompt_generation()

### Community 23 - "default_taxonomy"
Cohesion: 0.20
Nodes (6): default_taxonomy(), taxonomy_to_yaml(), test_cli_setup_noninteractive_generates_structure(), test_default_taxonomy_exact_spelling(), test_default_taxonomy_matches_builtin_constants(), test_taxonomy_to_yaml_round_trip()

### Community 24 - "test_taxonomy.py"
Cohesion: 0.11
Nodes (16): load_taxonomy(), test_cli_sort_rejects_invalid_structure_file(), test_cli_sort_uses_configured_structure(), test_executor_loads_structure_file(), test_heuristic_hint_insurance_letter(), test_heuristic_medical_requires_specific_terms(), test_heuristic_resume_outranks_medical(), test_load_taxonomy_custom_yaml() (+8 more)

### Community 25 - "auto-file"
Cohesion: 0.15
Nodes (12): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, Naming (+4 more)

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 334 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FilePipelineExecutor` connect `FilePipelineExecutor` to `executor.py`, `TaxonomyRouter`, `FolderWatcher`, `LayaDispatcher`, `cli.py`, `test_understander.py`, `UnderstandingResult`, `AuditLedger`, `test_taxonomy.py`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 43 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.rollback_run` be split into smaller, more focused modules?**
  _Cohesion score 0.12802275960170698 - nodes in this community are weakly interconnected._
- **Why does `TaxonomyRouter` connect `TaxonomyRouter` to `executor.py`, `FilePipelineExecutor`, `Path`, `Taxonomy`, `default_taxonomy`, `test_taxonomy.py`, `_create_onnx_session`, `test_router_no_false_person_from_partial_name`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `TaxonomyRouter` (e.g. with `FilePipelineExecutor` and `Taxonomy`) actually correct?**
  _`TaxonomyRouter` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Should `FileMetadata` be split into smaller, more focused modules?**
  _Cohesion score 0.10631229235880399 - nodes in this community are weakly interconnected._