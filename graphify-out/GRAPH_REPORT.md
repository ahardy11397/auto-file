# Graph Report - auto-file  (2026-10-19)

## Corpus Check
- 41 files · ~36,385 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 829 nodes · 1944 edges · 35 communities (22 shown, 13 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 374 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `35a68787`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- .rollback_run
- ExtractedContent
- executor.py
- test_naming.py
- TaxonomyRouter
- FolderWatcher
- Six-Stage Processing Pipeline
- test_cli.py
- CLI Interface (typer/rich)
- test_router.py
- auto_file
- cli.py
- FilePipelineExecutor
- parse_llm_json_response
- Taxonomy
- _load_transformer_model
- load_taxonomy
- AuditLedger
- audit.py
- Path
- _norm
- ._understand_via_llama_server
- LlamaServerManager
- test_taxonomy.py
- auto-file
- conftest.py
- default_taxonomy
- _create_onnx_session
- _MockNdarray
- normalize_date_string
- test_understander.py
- _create_onnx_session
- _FakeResponse

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 62 edges
2. `FilePipelineExecutor` - 49 edges
3. `TaxonomyRouter` - 49 edges
4. `ExtractedContent` - 42 edges
5. `GemmaUnderstander` - 39 edges
6. `detect_file_metadata()` - 33 edges
7. `FileMetadata` - 31 edges
8. `FolderWatcher` - 31 edges
9. `load_taxonomy()` - 24 edges
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

## Communities (35 total, 13 thin omitted)

### Community 0 - ".rollback_run"
Cohesion: 0.15
Nodes (12): _sha256(), test_audit_lifecycle_and_rollback(), test_context_manager_support(), test_finish_run_auto_aggregates_counts(), test_rollback_collision_raises_strict(), test_rollback_collision_skips_when_not_strict(), test_rollback_hash_mismatch_raises_strict(), test_rollback_hash_mismatch_skips_when_not_strict() (+4 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.06
Nodes (35): detect_file_metadata(), FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor (+27 more)

### Community 2 - "executor.py"
Cohesion: 0.11
Nodes (8): resolve_target_filename(), ResolvedDestination, sanitize_slug(), resolve_destination(), route_destination(), sanitize_folder_name(), _clean_json_string(), test_resolve_no_collision()

### Community 3 - "test_naming.py"
Cohesion: 0.10
Nodes (12): test_compute_file_sha256(), test_resolve_case_insensitive_collision(), test_resolve_collision_different_hash(), test_resolve_collision_identical_hash(), test_resolve_destination_dir_does_not_exist(), test_resolve_duplicate_found_at_numbered_suffix(), test_resolve_empty_slug_with_date_defaults_to_document(), test_resolve_extension_normalization() (+4 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.10
Nodes (21): TaxonomyRouter, test_route_all_people(), test_route_exact_structure_spelling(), test_route_financial_bank_statement(), test_route_financial_bills(), test_route_financial_documents_by_entity(), test_route_financial_misc(), test_route_financial_receipts_by_entity() (+13 more)

### Community 5 - "FolderWatcher"
Cohesion: 0.05
Nodes (17): FolderWatcher, _InboxEventHandler, test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest(), test_watcher_boundary_checks_and_nested_target_root(), test_watcher_context_manager() (+9 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.16
Nodes (11): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+3 more)

### Community 7 - "test_cli.py"
Cohesion: 0.07
Nodes (16): test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_no_args(), test_cli_sort_directory(), test_cli_sort_failure_displays_dash_in_table(), test_cli_sort_missing_dest_errors() (+8 more)

### Community 9 - "test_router.py"
Cohesion: 0.14
Nodes (12): dispatch_tool(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension(), test_dispatch_standalone_function() (+4 more)

### Community 12 - "cli.py"
Cohesion: 0.07
Nodes (24): Config-Driven Folder Structure — Design (2026-10-18), Decisions, Intent, Personal deployment (Kirby), Watcher loop guard (directional), YAML schema, config(), _llm_server_config() (+16 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.06
Nodes (29): FilePipelineExecutor, PipelineResult, compute_file_sha256(), _make_executor(), _RoutingStubUnderstander, test_llm_routing_invalid_folder_gates_to_needs_review(), test_llm_routing_moves_to_chosen_folder(), test_llm_routing_none_gates_to_needs_review() (+21 more)

### Community 14 - "parse_llm_json_response"
Cohesion: 0.09
Nodes (12): parse_llm_json_response(), understand_content(), UnderstandingResult, test_parse_conversational_wrapped_json(), test_parse_empty_and_garbage_input_safety(), test_parse_entities_normalization(), test_parse_json_with_trailing_commas(), test_parse_llm_json_response_with_comments_before_brace_in_code_fence() (+4 more)

### Community 16 - "_load_transformer_model"
Cohesion: 0.12
Nodes (4): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only(), test_understanding_result_to_dict()

### Community 17 - "load_taxonomy"
Cohesion: 0.18
Nodes (7): load_taxonomy(), _parse_folder_spec(), test_load_taxonomy_missing_file(), test_load_taxonomy_missing_roots(), test_router_insurance_letter_routes_to_insurance_child(), test_router_root_keywords_route_traffic(), test_router_scanned_document_files_by_filename()

### Community 18 - "AuditLedger"
Cohesion: 0.11
Nodes (7): history(), AuditLedger, test_empty_database_rollback(), test_finish_run_and_get_history(), test_cli_history_with_run_id(), test_cli_live_sort_single_file(), test_cli_undo_by_run_id()

### Community 19 - "audit.py"
Cohesion: 0.16
Nodes (5): AuditError, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError

### Community 23 - "LlamaServerManager"
Cohesion: 0.15
Nodes (3): LlamaServerManager, test_llama_server_manager_bad_binary_falls_back(), test_llama_server_manager_url_and_idle()

### Community 24 - "test_taxonomy.py"
Cohesion: 0.16
Nodes (9): test_cli_sort_rejects_invalid_structure_file(), test_cli_sort_uses_configured_structure(), test_executor_loads_structure_file(), test_heuristic_hint_insurance_letter(), test_heuristic_medical_requires_specific_terms(), test_heuristic_resume_outranks_medical(), test_load_taxonomy_custom_yaml(), test_resolve_destination_structure_argument() (+1 more)

### Community 25 - "auto-file"
Cohesion: 0.15
Nodes (12): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, Naming (+4 more)

### Community 27 - "default_taxonomy"
Cohesion: 0.25
Nodes (6): default_taxonomy(), taxonomy_to_yaml(), test_cli_setup_noninteractive_generates_structure(), test_default_taxonomy_exact_spelling(), test_default_taxonomy_matches_builtin_constants(), test_taxonomy_to_yaml_round_trip()

### Community 30 - "normalize_date_string"
Cohesion: 0.18
Nodes (5): _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text(), normalize_date_string(), test_parse_date_normalization_formats()

### Community 31 - "test_understander.py"
Cohesion: 0.08
Nodes (20): GemmaUnderstander, _content(), test_deterministic_rich_generic_text_is_understood(), test_deterministic_scan_without_text_is_not_understood(), test_deterministic_specific_category_is_understood(), test_llama_server_path_parses_understanding(), test_llama_server_unreachable_falls_back_to_deterministic(), test_neural_empty_output_is_not_understood() (+12 more)

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 364 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FilePipelineExecutor` connect `FilePipelineExecutor` to `executor.py`, `TaxonomyRouter`, `FolderWatcher`, `test_router.py`, `cli.py`, `AuditLedger`, `test_taxonomy.py`, `test_understander.py`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Are the 44 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 44 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.061748195669607056 - nodes in this community are weakly interconnected._
- **Why does `TaxonomyRouter` connect `TaxonomyRouter` to `executor.py`, `FilePipelineExecutor`, `Taxonomy`, `load_taxonomy`, `Path`, `_create_onnx_session`, `_MockNdarray`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 39 inferred relationships involving `FilePipelineExecutor` (e.g. with `sort()` and `watch()`) actually correct?**
  _`FilePipelineExecutor` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Should `executor.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10810810810810811 - nodes in this community are weakly interconnected._