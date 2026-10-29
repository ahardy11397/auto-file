# Graph Report - auto-file  (2026-10-29)

## Corpus Check
- 41 files · ~41,381 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 946 nodes · 2206 edges · 38 communities (27 shown, 11 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 422 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `409c03fe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuditLedger
- ExtractedContent
- executor.py
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
- UnderstandingResult
- Taxonomy
- Path
- load_taxonomy
- detect_file_metadata
- _load_transformer_model
- _route
- _StubLLMServer
- test_manager_never_kills_a_foreign_pid_from_the_pidfile
- LlamaServerManager
- test_taxonomy.py
- auto-file
- test_route_with_llama_unreachable_when_server_is_down
- taxonomy_to_yaml
- child_key
- _MockNdarray
- understander.py
- test_understander.py
- _create_onnx_session
- test_heuristic_medical_requires_specific_terms
- _FakeResponse
- test_heuristic_resume_outranks_medical

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 67 edges
2. `FilePipelineExecutor` - 54 edges
3. `GemmaUnderstander` - 52 edges
4. `TaxonomyRouter` - 49 edges
5. `ExtractedContent` - 42 edges
6. `FolderWatcher` - 34 edges
7. `detect_file_metadata()` - 33 edges
8. `FileMetadata` - 31 edges
9. `load_taxonomy()` - 31 edges
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

## Communities (38 total, 11 thin omitted)

### Community 0 - "AuditLedger"
Cohesion: 0.06
Nodes (21): AuditError, AuditLedger, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError, _mock_understander(), _sha256() (+13 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.11
Nodes (9): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor (+1 more)

### Community 2 - "executor.py"
Cohesion: 0.16
Nodes (4): ResolvedDestination, sanitize_slug(), resolve_destination(), route_destination()

### Community 3 - "resolve_target_filename"
Cohesion: 0.09
Nodes (14): resolve_target_filename(), test_compute_file_sha256(), test_resolve_case_insensitive_collision(), test_resolve_collision_different_hash(), test_resolve_collision_identical_hash(), test_resolve_destination_dir_does_not_exist(), test_resolve_duplicate_found_at_numbered_suffix(), test_resolve_empty_slug_with_date_defaults_to_document() (+6 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.11
Nodes (23): TaxonomyRouter, test_route_all_people(), test_route_exact_structure_spelling(), test_route_financial_bank_statement(), test_route_financial_bills(), test_route_financial_documents_by_entity(), test_route_financial_misc(), test_route_financial_receipts_by_entity() (+15 more)

### Community 5 - "FolderWatcher"
Cohesion: 0.05
Nodes (20): PipelineResult, FolderWatcher, _InboxEventHandler, test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest(), test_watcher_boundary_checks_and_nested_target_root() (+12 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.16
Nodes (11): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+3 more)

### Community 7 - "test_cli.py"
Cohesion: 0.06
Nodes (25): _free_port(), _install_fake_llama_server(), _port_is_free(), test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_history_with_run_id() (+17 more)

### Community 9 - "LayaDispatcher"
Cohesion: 0.12
Nodes (13): _create_onnx_session(), dispatch_tool(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension() (+5 more)

### Community 12 - "cli.py"
Cohesion: 0.06
Nodes (27): Config-Driven Folder Structure — Design (2026-10-18), Decisions, Intent, Personal deployment (Kirby), Watcher loop guard (directional), YAML schema, config(), _default_llm_binary() (+19 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.06
Nodes (30): FilePipelineExecutor, compute_file_sha256(), _make_executor(), _RoutingStubUnderstander, test_llm_routing_invalid_folder_gates_to_needs_review(), test_llm_routing_moves_to_chosen_folder(), test_llm_routing_none_gates_to_needs_review(), test_llm_routing_unreachable_falls_back_to_keyword_router() (+22 more)

### Community 14 - "UnderstandingResult"
Cohesion: 0.13
Nodes (7): understand_content(), UnderstandingResult, test_parse_empty_and_garbage_input_safety(), test_parse_malformed_json_fallback(), test_parse_valid_json_response(), test_understander_callable_interface(), test_understander_standalone_function()

### Community 15 - "Taxonomy"
Cohesion: 0.09
Nodes (4): _matches(), _norm(), Taxonomy, test_custom_taxonomy_is_valid_folder_unknown_root()

### Community 16 - "Path"
Cohesion: 0.11
Nodes (3): first_entity(), sanitize_folder_name(), test_sanitize_folder_name_rejects_dot_and_dotdot()

### Community 17 - "load_taxonomy"
Cohesion: 0.15
Nodes (10): load_taxonomy(), test_cli_setup_noninteractive_generates_structure(), test_dynamic_paths_lists_dynamic_folders(), test_dynamic_taxonomy_grandchildren_still_win_over_dynamic_component(), test_every_listed_path_is_accepted_by_the_validator(), test_is_valid_folder_accepts_dynamic_component(), test_is_valid_folder_rejects_dot_component_in_dynamic_folder(), test_load_taxonomy_missing_file() (+2 more)

### Community 18 - "detect_file_metadata"
Cohesion: 0.12
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 19 - "_load_transformer_model"
Cohesion: 0.10
Nodes (4): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only(), test_understanding_result_to_dict()

### Community 20 - "_route"
Cohesion: 0.16
Nodes (10): _route(), stub_llm_server(), test_route_with_llama_counts_as_in_flight_request(), test_route_with_llama_parses_fenced_json(), test_route_with_llama_parses_plain_json(), test_route_with_llama_prompt_advertises_dynamic_folders(), test_route_with_llama_prompt_lists_the_real_tree(), test_route_with_llama_reports_none_when_model_declines() (+2 more)

### Community 21 - "_StubLLMServer"
Cohesion: 0.28
Nodes (5): _make(), _StubLLMServer, do_GET(), do_POST(), _send()

### Community 22 - "test_manager_never_kills_a_foreign_pid_from_the_pidfile"
Cohesion: 0.25
Nodes (3): test_manager_never_kills_a_foreign_pid_from_the_pidfile(), test_understander_shutdown_server_stops_the_manager(), _write_fake_llama_server()

### Community 23 - "LlamaServerManager"
Cohesion: 0.09
Nodes (5): LlamaServerManager, test_llama_server_manager_bad_binary_falls_back(), test_llama_server_manager_url_and_idle(), test_manager_kills_the_orphan_it_started(), test_manager_pidfile_is_scoped_to_the_port()

### Community 24 - "test_taxonomy.py"
Cohesion: 0.11
Nodes (19): default_taxonomy(), test_all_paths_covers_roots_children_grandchildren_and_people(), test_all_paths_uses_custom_people(), test_cli_sort_rejects_invalid_structure_file(), test_cli_sort_uses_configured_structure(), test_default_taxonomy_exact_spelling(), test_default_taxonomy_matches_builtin_constants(), test_dynamic_paths_empty_for_default_taxonomy() (+11 more)

### Community 25 - "auto-file"
Cohesion: 0.12
Nodes (16): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, llama.cpp (recommended) (+8 more)

### Community 26 - "test_route_with_llama_unreachable_when_server_is_down"
Cohesion: 0.25
Nodes (3): _free_port(), test_has_llm_routing_is_false_without_an_llm(), test_route_with_llama_unreachable_when_server_is_down()

### Community 27 - "taxonomy_to_yaml"
Cohesion: 0.40
Nodes (3): taxonomy_to_yaml(), test_taxonomy_to_yaml_emits_dynamic_flag(), test_taxonomy_to_yaml_round_trip()

### Community 30 - "understander.py"
Cohesion: 0.08
Nodes (14): _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text(), _has_structured_json(), _is_informative(), normalize_date_string(), parse_llm_json_response() (+6 more)

### Community 31 - "test_understander.py"
Cohesion: 0.08
Nodes (22): GemmaUnderstander, _content(), test_deterministic_rich_generic_text_is_understood(), test_deterministic_scan_without_text_is_not_understood(), test_deterministic_specific_category_is_understood(), test_llama_server_generic_category_still_counts_as_understood(), test_llama_server_path_parses_understanding(), test_llama_server_unreachable_falls_back_to_deterministic() (+14 more)

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 412 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FilePipelineExecutor` connect `FilePipelineExecutor` to `AuditLedger`, `executor.py`, `TaxonomyRouter`, `FolderWatcher`, `LayaDispatcher`, `cli.py`, `test_taxonomy.py`, `test_understander.py`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 49 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AuditLedger` be split into smaller, more focused modules?**
  _Cohesion score 0.05878332194121668 - nodes in this community are weakly interconnected._
- **Why does `GemmaUnderstander` connect `test_understander.py` to `ExtractedContent`, `executor.py`, `FilePipelineExecutor`, `UnderstandingResult`, `_load_transformer_model`, `_route`, `test_manager_never_kills_a_foreign_pid_from_the_pidfile`, `test_route_with_llama_unreachable_when_server_is_down`, `understander.py`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 43 inferred relationships involving `FilePipelineExecutor` (e.g. with `sort()` and `watch()`) actually correct?**
  _`FilePipelineExecutor` has 43 INFERRED edges - model-reasoned connections that need verification._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.11008325624421832 - nodes in this community are weakly interconnected._