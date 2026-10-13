"""Core business logic for auto-file."""

from auto_file.core.detector import FileMetadata, detect_file_metadata
from auto_file.core.dispatcher import LayaDispatcher, dispatch_tool
from auto_file.core.naming import ResolvedDestination, resolve_target_filename, sanitize_slug
from auto_file.core.router import TaxonomyRouter, resolve_destination, route_destination

__all__ = [
    "FileMetadata",
    "detect_file_metadata",
    "LayaDispatcher",
    "dispatch_tool",
    "ResolvedDestination",
    "resolve_target_filename",
    "sanitize_slug",
    "TaxonomyRouter",
    "resolve_destination",
    "route_destination",
]
