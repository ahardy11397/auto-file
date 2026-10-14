# Graph Report - auto-file  (2026-10-13)

## Corpus Check
- 33 files · ~21,373 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: (none) 1, .lock 1)

## Summary
- 468 nodes · 1112 edges · 19 communities (14 shown, 5 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 220 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9da6c93a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuditLedger
- ExtractedContent
- detect_file_metadata
- resolve_target_filename
- TaxonomyRouter
- LayaDispatcher
- Six-Stage Processing Pipeline
- CLI Interface (typer/rich)
- understander.py
- auto_file
- auto-file
- FilePipelineExecutor
- GemmaUnderstander
- test_understander.py
- _load_transformer_model
- UnderstandingResult
- .generate_prompt

## God Nodes (most connected - your core abstractions)
1. `ExtractedContent` - 40 edges
2. `AuditLedger` - 38 edges
3. `TaxonomyRouter` - 34 edges
4. `detect_file_metadata()` - 33 edges
5. `FileMetadata` - 31 edges
6. `GemmaUnderstander` - 28 edges
7. `FilePipelineExecutor` - 25 edges
8. `get_extractor_for_tool()` - 22 edges
9. `LayaDispatcher` - 20 edges
10. `parse_llm_json_response()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `test_detect_text_file()` --uses--> `FileMetadata`  [INFERRED]
  tests/test_detector.py → src/auto_file/core/detector.py
- `_make_metadata()` --uses--> `FileMetadata`  [INFERRED]
  tests/test_router.py → src/auto_file/core/detector.py
- `test_pipeline_date_precedence_exif_date()` --uses--> `ExtractedContent`  [INFERRED]
  tests/test_executor.py → src/auto_file/core/extractors/base.py
- `test_understander_callable_interface()` --uses--> `ExtractedContent`  [INFERRED]
  tests/test_understander.py → src/auto_file/core/extractors/base.py
- `test_understander_custom_mock_response()` --uses--> `ExtractedContent`  [INFERRED]
  tests/test_understander.py → src/auto_file/core/extractors/base.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Laya Used Twice: Dispatch + Route** — idea_laya_decision_model, docs_superpowers_specs_2026_10_09_auto_file_system_design_dispatch_stage, docs_superpowers_specs_2026_10_09_auto_file_system_design_route_stage [EXTRACTED 1.00]
- **Reversibility Guarantee (hash + ledger + undo)** — docs_superpowers_specs_2026_10_09_auto_file_system_design_sqlite_audit_ledger, docs_superpowers_plans_2026_10_12_auto_file_system_rollback_safety, docs_superpowers_specs_2026_10_09_auto_file_system_design_execute_audit_stage [EXTRACTED 1.00]

## Communities (19 total, 5 thin omitted)

### Community 0 - "AuditLedger"
Cohesion: 0.07
Nodes (20): AuditError, AuditLedger, RollbackCollisionError, RollbackError, RollbackMissingFileError, RollbackVerificationError, _sha256(), test_audit_lifecycle_and_rollback() (+12 more)

### Community 1 - "ExtractedContent"
Cohesion: 0.11
Nodes (9): FileMetadata, AudioExtractor, _get_tag_value(), BaseExtractor, ExtractedContent, FallbackExtractor, ImageExtractor, PDFExtractor (+1 more)

### Community 2 - "detect_file_metadata"
Cohesion: 0.12
Nodes (26): detect_file_metadata(), get_extractor_for_tool(), test_detect_exact_sha256(), test_detect_extensionless_file(), test_detect_fallback_mimetype(), test_detect_misnamed_file(), test_detect_nonexistent_file(), test_detect_text_file() (+18 more)

### Community 3 - "resolve_target_filename"
Cohesion: 0.10
Nodes (13): compute_file_sha256(), resolve_target_filename(), test_compute_file_sha256(), test_resolve_case_insensitive_collision(), test_resolve_collision_different_hash(), test_resolve_collision_identical_hash(), test_resolve_destination_dir_does_not_exist(), test_resolve_duplicate_found_at_numbered_suffix() (+5 more)

### Community 4 - "TaxonomyRouter"
Cohesion: 0.06
Nodes (19): _create_onnx_session(), resolve_destination(), route_destination(), sanitize_folder_name(), TaxonomyRouter, test_route_all_people(), test_route_exact_structure_spelling(), test_route_financial_bank_statement() (+11 more)

### Community 5 - "LayaDispatcher"
Cohesion: 0.13
Nodes (12): _create_onnx_session(), dispatch_tool(), LayaDispatcher, _make_metadata(), test_dispatch_audio_files(), test_dispatch_fallback_extractor(), test_dispatch_images(), test_dispatch_pdf_by_mime_and_extension() (+4 more)

### Community 6 - "Six-Stage Processing Pipeline"
Cohesion: 0.15
Nodes (13): Graphify Project Rules, Implementation Plan (10 TDD Tasks), Auto-File System Design Spec, Detect Stage, Dispatch Stage (Laya tool choice), Execute & Audit Stage, Extract Stage (PDF/Image/Text/Audio/Fallback), Route Stage (hierarchical taxonomy) (+5 more)

### Community 9 - "understander.py"
Cohesion: 0.15
Nodes (8): ResolvedDestination, sanitize_slug(), _clean_json_string(), _extract_category_hint_from_text(), _extract_date_from_text(), _extract_entities_from_text(), normalize_date_string(), parse_llm_json_response()

### Community 12 - "auto-file"
Cohesion: 0.20
Nodes (9): auto-file, Design docs, Development, How it works, Installation, Naming, Project layout, Safety & reversibility (+1 more)

### Community 13 - "FilePipelineExecutor"
Cohesion: 0.07
Nodes (18): FilePipelineExecutor, PipelineResult, test_pipeline_audit_rollback_restores_files(), test_pipeline_batch_process_directory(), test_pipeline_batch_process_directory_dry_run(), test_pipeline_batch_process_directory_recursive(), test_pipeline_collision_different_content(), test_pipeline_date_precedence_content_date() (+10 more)

### Community 14 - "GemmaUnderstander"
Cohesion: 0.12
Nodes (10): GemmaUnderstander, test_understander_custom_mock_response(), test_understander_deterministic_audio_metadata(), test_understander_deterministic_image_with_exif(), test_understander_deterministic_markdown_header_slug(), test_understander_deterministic_medical_record(), test_understander_deterministic_text_bank_statement(), test_understander_image_without_exif() (+2 more)

### Community 15 - "test_understander.py"
Cohesion: 0.12
Nodes (7): test_parse_conversational_wrapped_json(), test_parse_date_normalization_formats(), test_parse_empty_and_garbage_input_safety(), test_parse_entities_normalization(), test_parse_json_with_trailing_commas(), test_parse_raw_json_without_fences(), test_understander_lazy_initialization()

### Community 16 - "_load_transformer_model"
Cohesion: 0.15
Nodes (3): _load_transformer_model(), test_understander_model_loading_and_cuda_oom_fallback(), test_understanding_result_to_dict()

### Community 17 - "UnderstandingResult"
Cohesion: 0.18
Nodes (6): understand_content(), UnderstandingResult, test_parse_malformed_json_fallback(), test_parse_valid_json_response(), test_understander_callable_interface(), test_understander_standalone_function()

## Knowledge Gaps
- **6 isolated node(s):** `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)`, `Graphify Project Rules`, `CLI Interface (typer/rich)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 201 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuditLedger` connect `AuditLedger` to `TaxonomyRouter`, `FilePipelineExecutor`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `ExtractedContent` (e.g. with `AudioExtractor` and `FallbackExtractor`) actually correct?**
  _`ExtractedContent` has 21 INFERRED edges - model-reasoned connections that need verification._
- **What connects `auto_file`, `Detect Stage`, `Extract Stage (PDF/Image/Text/Audio/Fallback)` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AuditLedger` be split into smaller, more focused modules?**
  _Cohesion score 0.06777493606138107 - nodes in this community are weakly interconnected._
- **Why does `TaxonomyRouter` connect `TaxonomyRouter` to `understander.py`, `FilePipelineExecutor`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `AuditLedger` (e.g. with `FilePipelineExecutor` and `test_audit_lifecycle_and_rollback()`) actually correct?**
  _`AuditLedger` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Should `ExtractedContent` be split into smaller, more focused modules?**
  _Cohesion score 0.11304347826086956 - nodes in this community are weakly interconnected._