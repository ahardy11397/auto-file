"""Core business logic for auto-file."""

from auto_file.core.detector import FileMetadata, detect_file_metadata
from auto_file.core.dispatcher import LayaDispatcher, dispatch_tool
from auto_file.core.executor import FilePipelineExecutor, PipelineResult
from auto_file.core.naming import ResolvedDestination, resolve_target_filename, sanitize_slug
from auto_file.core.router import TaxonomyRouter, resolve_destination, route_destination
from auto_file.core.understander import (
    GemmaUnderstander,
    UnderstandingResult,
    normalize_date_string,
    parse_llm_json_response,
    understand_content,
)
from auto_file.core.watcher import FolderWatcher

__all__ = [
    "FileMetadata",
    "detect_file_metadata",
    "LayaDispatcher",
    "dispatch_tool",
    "FilePipelineExecutor",
    "PipelineResult",
    "ResolvedDestination",
    "resolve_target_filename",
    "sanitize_slug",
    "TaxonomyRouter",
    "resolve_destination",
    "route_destination",
    "GemmaUnderstander",
    "UnderstandingResult",
    "normalize_date_string",
    "parse_llm_json_response",
    "understand_content",
    "FolderWatcher",
]

