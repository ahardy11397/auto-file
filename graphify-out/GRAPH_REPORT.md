# Graph Report - auto-file  (2026-10-21)

## Corpus Check
- 41 files · ~40,963 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 938 nodes · 2178 edges · 33 communities (27 shown, 6 thin omitted)
- Extraction: 81% EXTRACTED · 19% INFERRED · 0% AMBIGUOUS · INFERRED: 409 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `74b4cce0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuditLedger
- ExtractedContent
- understander.py
- resolve_target_filename
- TaxonomyRouter
- FolderWatcher
- Six-Stage Processing Pipeline
- test_cli.py
- CLI Interface (typer/rich)
- FileMetadata
- auto_file
- cli.py
- FilePipelineExecutor
- UnderstandingResult
- Taxonomy
- _load_transformer_model
- load_taxonomy
- detect_file_metadata
- ._chat
- _route
- .__init__
- .generate_prompt
- LlamaServerManager
- test_taxonomy.py
- auto-file
- test_route_with_llama_unreachable_when_server_is_down
- default_taxonomy
- _content
- _StubLLMServer
- test_understander.py
- GemmaUnderstander
- _FakeResponse

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 64 edges
2. `GemmaUnderstander` - 52 edges
3. `FilePipelineExecutor` - 51 edges
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
- `test_llama_server_manager_url_and_idle()` --uses--> `LlamaServerManager`  [INFERRED]
  tests/test_understander.py → src/auto_file/core/understander.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Laya Used Twice: Dispatch + Route** — idea_laya_decision_model, docs_superpowers_specs_2026_10_09_auto_file_system_design_dispatch_stage, docs_superpowers_specs_2026_10_09_auto_file_system_design_route_stage [EXTRACTED 1.00]
- **Reversibility Guarantee (hash + ledger + undo)** — docs_superpowers_specs_2026_10_09_auto_file_system_design_sqlite_audit_ledger, docs_superpowers_plans_2026_10_12_auto_file_system_rollback_safety, docs_superpowers_specs_2026_10_09_auto_file_system_design_execute_audit_stage [EXTRACTED 1.00]

## Communities (33 total, 6 thin omitted)

### Community 0 - "AuditLedger"
Cohesion: 0.06
Nodes (21): AuditError, AuditLedger, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError, _mock_understander(), _sha256() (+13 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.10
Nodes (8): AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor, TextExtractor

### Community 2 - "understander.py"
Cohesion: 0.09
Nodes (10): ResolvedDestination, sanitize_slug(), resolve_destination(), route_destination(), _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text() (+2 more)

### Community 3 - "resolve_target_filename"
Cohesion: 0.09
Nodes (14): resolve_target_filename(), test_compute_file_sha256(), test_resolve_case_insensitive_collision(), test_resolve_collision_different_hash(), test_resolve_collision_identical_hash(), test_resolve_destination_dir_does_not_exist(), test_resolve_duplicate_found_at_numbered_suffix(), test_resolve_empty_slug_with_date_defaults_to_document() (+6 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.05
Nodes (27): _create_onnx_session(), TaxonomyRouter, first_entity(), sanitize_folder_name(), _MockNdarray, test_dispatch_standalone_function(), test_route_all_people(), test_route_exact_structure_spelling() (+19 more)

### Community 5 - "FolderWatcher"
Cohesion: 0.05
Nodes (22): Config-Driven Folder Structure — Design (2026-10-18), Intent, Personal deployment (Kirby), Watcher loop guard (directional), YAML schema, FolderWatcher, _InboxEventHandler, test_cli_watch_clean_interrupt() (+14 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.16
Nodes (11): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+3 more)

### Community 7 - "test_cli.py"
Cohesion: 0.06
Nodes (25): _free_port(), _install_fake_llama_server(), _port_is_free(), test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_history_with_run_id() (+17 more)

### Community 9 - "FileMetadata"
Cohesion: 0.13
Nodes (13): FileMetadata, _create_onnx_session(), dispatch_tool(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images() (+5 more)

### Community 12 - "cli.py"
Cohesion: 0.07
Nodes (22): Decisions, config(), _default_llm_binary(), _guess_mmproj(), history(), _llm_settings(), main(), _resolved_structure() (+14 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.06
Nodes (30): FilePipelineExecutor, PipelineResult, compute_file_sha256(), _make_executor(), _RoutingStubUnderstander, test_llm_routing_invalid_folder_gates_to_needs_review(), test_llm_routing_moves_to_chosen_folder(), test_llm_routing_none_gates_to_needs_review() (+22 more)

### Community 14 - "UnderstandingResult"
Cohesion: 0.12
Nodes (8): _has_structured_json(), _is_informative(), understand_content(), UnderstandingResult, test_parse_empty_and_garbage_input_safety(), test_parse_malformed_json_fallback(), test_parse_valid_json_response(), test_understander_standalone_function()

### Community 15 - "Taxonomy"
Cohesion: 0.08
Nodes (6): child_key(), _matches(), _norm(), _parse_folder_spec(), Taxonomy, test_custom_taxonomy_is_valid_folder_unknown_root()

### Community 16 - "_load_transformer_model"
Cohesion: 0.22
Nodes (3): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understander_model_loading_passes_local_files_only()

### Community 17 - "load_taxonomy"
Cohesion: 0.15
Nodes (11): load_taxonomy(), test_dynamic_paths_lists_dynamic_folders(), test_dynamic_taxonomy_grandchildren_still_win_over_dynamic_component(), test_every_listed_path_is_accepted_by_the_validator(), test_is_valid_folder_accepts_dynamic_component(), test_is_valid_folder_rejects_dot_component_in_dynamic_folder(), test_router_insurance_letter_routes_to_insurance_child(), test_router_root_keywords_route_traffic() (+3 more)

### Community 18 - "detect_file_metadata"
Cohesion: 0.12
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 20 - "_route"
Cohesion: 0.16
Nodes (10): _route(), stub_llm_server(), test_route_with_llama_counts_as_in_flight_request(), test_route_with_llama_parses_fenced_json(), test_route_with_llama_parses_plain_json(), test_route_with_llama_prompt_advertises_dynamic_folders(), test_route_with_llama_prompt_lists_the_real_tree(), test_route_with_llama_reports_none_when_model_declines() (+2 more)

### Community 21 - ".__init__"
Cohesion: 0.60
Nodes (3): do_GET(), do_POST(), _send()

### Community 23 - "LlamaServerManager"
Cohesion: 0.08
Nodes (6): LlamaServerManager, test_llama_server_manager_bad_binary_falls_back(), test_manager_kills_the_orphan_it_started(), test_manager_never_kills_a_foreign_pid_from_the_pidfile(), test_manager_pidfile_is_scoped_to_the_port(), _write_fake_llama_server()

### Community 24 - "test_taxonomy.py"
Cohesion: 0.12
Nodes (13): test_all_paths_uses_custom_people(), test_cli_sort_rejects_invalid_structure_file(), test_cli_sort_uses_configured_structure(), test_executor_loads_structure_file(), test_heuristic_hint_insurance_letter(), test_heuristic_medical_requires_specific_terms(), test_heuristic_resume_outranks_medical(), test_load_taxonomy_custom_yaml() (+5 more)

### Community 25 - "auto-file"
Cohesion: 0.12
Nodes (16): auto-file, CLI Usage, Design docs, Development & Testing, Folder structure file, How it works, Installation, llama.cpp (recommended) (+8 more)

### Community 26 - "test_route_with_llama_unreachable_when_server_is_down"
Cohesion: 0.25
Nodes (3): _free_port(), test_has_llm_routing_is_false_without_an_llm(), test_route_with_llama_unreachable_when_server_is_down()

### Community 27 - "default_taxonomy"
Cohesion: 0.12
Nodes (13): default_taxonomy(), taxonomy_to_yaml(), test_all_paths_covers_roots_children_grandchildren_and_people(), test_cli_setup_noninteractive_generates_structure(), test_default_taxonomy_exact_spelling(), test_default_taxonomy_matches_builtin_constants(), test_dynamic_paths_empty_for_default_taxonomy(), test_is_valid_folder_accepts_person_subfolder() (+5 more)

### Community 28 - "_content"
Cohesion: 0.15
Nodes (7): _content(), test_deterministic_rich_generic_text_is_understood(), test_deterministic_scan_without_text_is_not_understood(), test_deterministic_specific_category_is_understood(), test_llama_server_unreachable_falls_back_to_deterministic(), test_neural_empty_output_is_not_understood(), test_understander_ondemand_spawn_failure_uses_deterministic_gate()

### Community 30 - "test_understander.py"
Cohesion: 0.10
Nodes (9): test_llama_server_manager_url_and_idle(), test_parse_conversational_wrapped_json(), test_parse_date_normalization_formats(), test_parse_entities_normalization(), test_parse_json_with_trailing_commas(), test_parse_llm_json_response_with_comments_before_brace_in_code_fence(), test_parse_raw_json_without_fences(), test_understander_callable_interface() (+1 more)

### Community 31 - "GemmaUnderstander"
Cohesion: 0.11
Nodes (11): GemmaUnderstander, test_understander_custom_mock_response(), test_understander_deterministic_audio_metadata(), test_understander_deterministic_image_with_exif(), test_understander_deterministic_markdown_header_slug(), test_understander_deterministic_medical_record(), test_understander_deterministic_text_bank_statement(), test_understander_image_without_exif() (+3 more)

### Community 36 - "_FakeResponse"
Cohesion: 0.22
Nodes (3): _FakeResponse, test_llama_server_generic_category_still_counts_as_understood(), test_llama_server_path_parses_understanding()

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 408 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FilePipelineExecutor` connect `FilePipelineExecutor` to `AuditLedger`, `understander.py`, `TaxonomyRouter`, `FolderWatcher`, `FileMetadata`, `cli.py`, `test_taxonomy.py`, `GemmaUnderstander`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 46 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AuditLedger` be split into smaller, more focused modules?**
  _Cohesion score 0.05878332194121668 - nodes in this community are weakly interconnected._
- **Why does `GemmaUnderstander` connect `GemmaUnderstander` to `ExtractedContent`, `understander.py`, `_FakeResponse`, `FilePipelineExecutor`, `UnderstandingResult`, `_load_transformer_model`, `._chat`, `_route`, `.generate_prompt`, `test_route_with_llama_unreachable_when_server_is_down`, `_content`, `test_understander.py`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `GemmaUnderstander` (e.g. with `FilePipelineExecutor` and `ExtractedContent`) actually correct?**
  _`GemmaUnderstander` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.1014799154334038 - nodes in this community are weakly interconnected._