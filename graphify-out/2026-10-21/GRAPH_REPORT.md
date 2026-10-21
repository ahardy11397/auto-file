# Graph Report - auto-file  (2026-10-21)

## Corpus Check
- 41 files · ~40,792 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 934 nodes · 2165 edges · 36 communities (25 shown, 11 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 403 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `74b4cce0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuditLedger
- ExtractedContent
- understander.py
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
- UnderstandingResult
- Taxonomy
- _load_transformer_model
- load_taxonomy
- detect_file_metadata
- ._chat
- Path
- _StubLLMServer
- .generate_prompt
- LlamaServerManager
- test_taxonomy.py
- auto-file
- test_route_with_llama_unreachable_when_server_is_down
- child_key
- _create_onnx_session
- _MockNdarray
- test_understander.py
- GemmaUnderstander
- test_router_scanned_document_files_by_filename
- test_heuristic_resume_outranks_medical
- _FakeResponse

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 63 edges
2. `GemmaUnderstander` - 51 edges
3. `FilePipelineExecutor` - 50 edges
4. `TaxonomyRouter` - 49 edges
5. `ExtractedContent` - 42 edges
6. `detect_file_metadata()` - 33 edges
7. `FileMetadata` - 31 edges
8. `load_taxonomy()` - 31 edges
9. `FolderWatcher` - 31 edges
10. `LlamaServerManager` - 28 edges

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

## Communities (36 total, 11 thin omitted)

### Community 0 - "AuditLedger"
Cohesion: 0.07
Nodes (20): AuditError, AuditLedger, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError, _sha256(), test_audit_lifecycle_and_rollback() (+12 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.12
Nodes (9): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor (+1 more)

### Community 2 - "understander.py"
Cohesion: 0.13
Nodes (9): sanitize_slug(), _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text(), _has_structured_json(), _is_informative(), normalize_date_string() (+1 more)

### Community 3 - "executor.py"
Cohesion: 0.06
Nodes (20): dispatch_tool(), compute_file_sha256(), resolve_target_filename(), ResolvedDestination, resolve_destination(), route_destination(), sanitize_folder_name(), test_compute_file_sha256() (+12 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.12
Nodes (21): TaxonomyRouter, test_route_all_people(), test_route_exact_structure_spelling(), test_route_financial_bank_statement(), test_route_financial_bills(), test_route_financial_documents_by_entity(), test_route_financial_misc(), test_route_financial_receipts_by_entity() (+13 more)

### Community 5 - "FolderWatcher"
Cohesion: 0.05
Nodes (18): PipelineResult, FolderWatcher, _InboxEventHandler, test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest(), test_watcher_boundary_checks_and_nested_target_root() (+10 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.16
Nodes (11): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+3 more)

### Community 7 - "test_cli.py"
Cohesion: 0.05
Nodes (26): _mock_understander(), _free_port(), _install_fake_llama_server(), _port_is_free(), test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated() (+18 more)

### Community 9 - "LayaDispatcher"
Cohesion: 0.13
Nodes (12): _create_onnx_session(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension(), test_dispatch_standalone_function() (+4 more)

### Community 12 - "cli.py"
Cohesion: 0.06
Nodes (27): Config-Driven Folder Structure — Design (2026-10-18), Decisions, Intent, Personal deployment (Kirby), Watcher loop guard (directional), YAML schema, config(), _default_llm_binary() (+19 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.07
Nodes (27): FilePipelineExecutor, _make_executor(), _RoutingStubUnderstander, test_llm_routing_invalid_folder_gates_to_needs_review(), test_llm_routing_moves_to_chosen_folder(), test_llm_routing_none_gates_to_needs_review(), test_llm_routing_unreachable_falls_back_to_keyword_router(), test_pipeline_audit_rollback_restores_files() (+19 more)

### Community 14 - "UnderstandingResult"
Cohesion: 0.13
Nodes (8): understand_content(), UnderstandingResult, test_parse_empty_and_garbage_input_safety(), test_parse_malformed_json_fallback(), test_parse_valid_json_response(), test_understander_callable_interface(), test_understander_custom_mock_response(), test_understander_standalone_function()

### Community 15 - "Taxonomy"
Cohesion: 0.11
Nodes (4): _matches(), _norm(), Taxonomy, test_custom_taxonomy_is_valid_folder_unknown_root()

### Community 16 - "_load_transformer_model"
Cohesion: 0.22
Nodes (3): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only()

### Community 17 - "load_taxonomy"
Cohesion: 0.15
Nodes (10): load_taxonomy(), test_cli_setup_noninteractive_generates_structure(), test_dynamic_paths_lists_dynamic_folders(), test_dynamic_taxonomy_grandchildren_still_win_over_dynamic_component(), test_every_listed_path_is_accepted_by_the_validator(), test_is_valid_folder_accepts_dynamic_component(), test_is_valid_folder_rejects_dot_component_in_dynamic_folder(), test_load_taxonomy_missing_file() (+2 more)

### Community 18 - "detect_file_metadata"
Cohesion: 0.12
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 21 - "_StubLLMServer"
Cohesion: 0.28
Nodes (5): _make(), _StubLLMServer, do_GET(), do_POST(), _send()

### Community 23 - "LlamaServerManager"
Cohesion: 0.09
Nodes (5): LlamaServerManager, test_llama_server_manager_bad_binary_falls_back(), test_llama_server_manager_url_and_idle(), test_manager_kills_the_orphan_it_started(), test_manager_pidfile_is_scoped_to_the_port()

### Community 24 - "test_taxonomy.py"
Cohesion: 0.10
Nodes (20): default_taxonomy(), test_all_paths_covers_roots_children_grandchildren_and_people(), test_all_paths_uses_custom_people(), test_cli_sort_rejects_invalid_structure_file(), test_cli_sort_uses_configured_structure(), test_default_taxonomy_exact_spelling(), test_default_taxonomy_matches_builtin_constants(), test_dynamic_paths_empty_for_default_taxonomy() (+12 more)

### Community 25 - "auto-file"
Cohesion: 0.12
Nodes (16): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, llama.cpp (recommended) (+8 more)

### Community 26 - "test_route_with_llama_unreachable_when_server_is_down"
Cohesion: 0.25
Nodes (3): _free_port(), test_has_llm_routing_is_false_without_an_llm(), test_route_with_llama_unreachable_when_server_is_down()

### Community 27 - "child_key"
Cohesion: 0.18
Nodes (5): child_key(), _parse_folder_spec(), taxonomy_to_yaml(), test_taxonomy_to_yaml_emits_dynamic_flag(), test_taxonomy_to_yaml_round_trip()

### Community 30 - "test_understander.py"
Cohesion: 0.07
Nodes (19): _route(), stub_llm_server(), test_manager_never_kills_a_foreign_pid_from_the_pidfile(), test_parse_conversational_wrapped_json(), test_parse_date_normalization_formats(), test_parse_entities_normalization(), test_parse_json_with_trailing_commas(), test_parse_llm_json_response_with_comments_before_brace_in_code_fence() (+11 more)

### Community 31 - "GemmaUnderstander"
Cohesion: 0.08
Nodes (18): GemmaUnderstander, _content(), test_deterministic_rich_generic_text_is_understood(), test_deterministic_scan_without_text_is_not_understood(), test_deterministic_specific_category_is_understood(), test_llama_server_path_parses_understanding(), test_llama_server_unreachable_falls_back_to_deterministic(), test_neural_empty_output_is_not_understood() (+10 more)

### Community 32 - "test_router_scanned_document_files_by_filename"
Cohesion: 0.40
Nodes (3): test_router_insurance_letter_routes_to_insurance_child(), test_router_root_keywords_route_traffic(), test_router_scanned_document_files_by_filename()

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 406 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FilePipelineExecutor` connect `FilePipelineExecutor` to `AuditLedger`, `executor.py`, `TaxonomyRouter`, `FolderWatcher`, `LayaDispatcher`, `cli.py`, `test_taxonomy.py`, `GemmaUnderstander`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Are the 45 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 45 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AuditLedger` be split into smaller, more focused modules?**
  _Cohesion score 0.06692242114236999 - nodes in this community are weakly interconnected._
- **Why does `GemmaUnderstander` connect `GemmaUnderstander` to `ExtractedContent`, `understander.py`, `executor.py`, `FilePipelineExecutor`, `UnderstandingResult`, `_load_transformer_model`, `._chat`, `.generate_prompt`, `test_route_with_llama_unreachable_when_server_is_down`, `test_understander.py`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `GemmaUnderstander` (e.g. with `FilePipelineExecutor` and `ExtractedContent`) actually correct?**
  _`GemmaUnderstander` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.11616161616161616 - nodes in this community are weakly interconnected._