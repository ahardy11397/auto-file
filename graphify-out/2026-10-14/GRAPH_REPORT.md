# Graph Report - auto-file  (2026-10-14)

## Corpus Check
- 38 files · ~26,484 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 619 nodes · 1478 edges · 22 communities (17 shown, 5 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 305 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f2d15a82`
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
- ._understand_deterministic
- auto_file
- cli.py
- FilePipelineExecutor
- test_understander.py
- executor.py
- _load_transformer_model
- parse_llm_json_response
- AuditLedger
- audit.py
- UnderstandingResult
- test_parse_date_normalization_formats

## God Nodes (most connected - your core abstractions)
1. `AuditLedger` - 57 edges
2. `FilePipelineExecutor` - 41 edges
3. `ExtractedContent` - 40 edges
4. `TaxonomyRouter` - 34 edges
5. `detect_file_metadata()` - 33 edges
6. `FileMetadata` - 31 edges
7. `FolderWatcher` - 29 edges
8. `GemmaUnderstander` - 28 edges
9. `get_extractor_for_tool()` - 22 edges
10. `LayaDispatcher` - 20 edges

## Surprising Connections (you probably didn't know these)
- `Safety & reversibility` --references--> `undo()`  [INFERRED]
  README.md → src/auto_file/cli.py
- `Usage` --references--> `sort()`  [INFERRED]
  README.md → src/auto_file/cli.py
- `Usage` --references--> `history()`  [INFERRED]
  README.md → src/auto_file/cli.py
- `Usage` --references--> `undo()`  [INFERRED]
  README.md → src/auto_file/cli.py
- `Usage` --references--> `config()`  [INFERRED]
  README.md → src/auto_file/cli.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Laya Used Twice: Dispatch + Route** — idea_laya_decision_model, docs_superpowers_specs_2026_10_09_auto_file_system_design_dispatch_stage, docs_superpowers_specs_2026_10_09_auto_file_system_design_route_stage [EXTRACTED 1.00]
- **Reversibility Guarantee (hash + ledger + undo)** — docs_superpowers_specs_2026_10_09_auto_file_system_design_sqlite_audit_ledger, docs_superpowers_plans_2026_10_12_auto_file_system_rollback_safety, docs_superpowers_specs_2026_10_09_auto_file_system_design_execute_audit_stage [EXTRACTED 1.00]

## Communities (22 total, 5 thin omitted)

### Community 0 - ".rollback_run"
Cohesion: 0.14
Nodes (13): _sha256(), test_audit_lifecycle_and_rollback(), test_context_manager_support(), test_empty_database_rollback(), test_finish_run_auto_aggregates_counts(), test_rollback_collision_raises_strict(), test_rollback_collision_skips_when_not_strict(), test_rollback_hash_mismatch_raises_strict() (+5 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.12
Nodes (9): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor (+1 more)

### Community 2 - "detect_file_metadata"
Cohesion: 0.12
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 3 - "resolve_target_filename"
Cohesion: 0.10
Nodes (13): compute_file_sha256(), resolve_target_filename(), test_compute_file_sha256(), test_resolve_case_insensitive_collision(), test_resolve_collision_different_hash(), test_resolve_collision_identical_hash(), test_resolve_destination_dir_does_not_exist(), test_resolve_duplicate_found_at_numbered_suffix() (+5 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.05
Nodes (28): _create_onnx_session(), dispatch_tool(), LayaDispatcher, _create_onnx_session(), TaxonomyRouter, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor() (+20 more)

### Community 5 - "FolderWatcher"
Cohesion: 0.05
Nodes (18): PipelineResult, FolderWatcher, _InboxEventHandler, test_pipeline_result_dataclass_coercion(), test_cli_watch_clean_interrupt(), test_cli_watch_inbox_not_a_directory(), test_cli_watch_invalid_inbox(), test_cli_watch_missing_dest() (+10 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.15
Nodes (13): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+5 more)

### Community 7 - "test_cli.py"
Cohesion: 0.08
Nodes (14): test_cli_config_commands(), test_cli_dry_run_sort(), test_cli_help(), test_cli_history_empty_and_populated(), test_cli_no_args(), test_cli_sort_directory(), test_cli_sort_missing_dest_errors(), test_cli_sort_missing_file_errors() (+6 more)

### Community 12 - "cli.py"
Cohesion: 0.06
Nodes (24): auto-file, Design docs, Development, How it works, Installation, Naming, Project layout, Safety & reversibility (+16 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.10
Nodes (16): FilePipelineExecutor, test_pipeline_audit_rollback_restores_files(), test_pipeline_batch_process_directory(), test_pipeline_batch_process_directory_dry_run(), test_pipeline_batch_process_directory_recursive(), test_pipeline_collision_different_content(), test_pipeline_date_precedence_content_date(), test_pipeline_date_precedence_exif_date() (+8 more)

### Community 14 - "test_understander.py"
Cohesion: 0.10
Nodes (14): GemmaUnderstander, test_understander_callable_interface(), test_understander_custom_mock_response(), test_understander_deterministic_audio_metadata(), test_understander_deterministic_image_with_exif(), test_understander_deterministic_markdown_header_slug(), test_understander_deterministic_medical_record(), test_understander_deterministic_text_bank_statement() (+6 more)

### Community 15 - "executor.py"
Cohesion: 0.13
Nodes (7): ResolvedDestination, sanitize_slug(), resolve_destination(), route_destination(), sanitize_folder_name(), _extract_date_from_text(), normalize_date_string()

### Community 16 - "_load_transformer_model"
Cohesion: 0.15
Nodes (3): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understanding_result_to_dict()

### Community 17 - "parse_llm_json_response"
Cohesion: 0.12
Nodes (8): _clean_json_string(), parse_llm_json_response(), test_parse_conversational_wrapped_json(), test_parse_empty_and_garbage_input_safety(), test_parse_entities_normalization(), test_parse_json_with_trailing_commas(), test_parse_raw_json_without_fences(), test_parse_valid_json_response()

### Community 18 - "AuditLedger"
Cohesion: 0.11
Nodes (5): AuditLedger, test_finish_run_and_get_history(), test_cli_history_with_run_id(), test_cli_live_sort_single_file(), test_cli_undo_by_run_id()

### Community 19 - "audit.py"
Cohesion: 0.14
Nodes (4): AuditError, RollbackCollisionError, RollbackMissingFileError, RollbackVerificationError

### Community 20 - "UnderstandingResult"
Cohesion: 0.22
Nodes (4): understand_content(), UnderstandingResult, test_parse_malformed_json_fallback(), test_understander_standalone_function()

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 269 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditLedger` connect `AuditLedger` to `.rollback_run`, `FolderWatcher`, `test_cli.py`, `cli.py`, `FilePipelineExecutor`, `executor.py`, `audit.py`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Are the 40 inferred relationships involving `AuditLedger` (e.g. with `history()` and `sort()`) actually correct?**
  _`AuditLedger` has 40 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `.rollback_run` be split into smaller, more focused modules?**
  _Cohesion score 0.1411764705882353 - nodes in this community are weakly interconnected._
- **Why does `FilePipelineExecutor` connect `FilePipelineExecutor` to `TaxonomyRouter`, `FolderWatcher`, `cli.py`, `test_understander.py`, `executor.py`, `AuditLedger`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `FilePipelineExecutor` (e.g. with `sort()` and `watch()`) actually correct?**
  _`FilePipelineExecutor` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.11616161616161616 - nodes in this community are weakly interconnected._