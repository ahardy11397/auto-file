"""Fallback content extractor for unsupported or binary file types."""

from typing import Any

from auto_file.core.detector import FileMetadata
from auto_file.core.extractors.base import BaseExtractor, ExtractedContent


class FallbackExtractor(BaseExtractor):
    """Fallback extractor that captures raw header snippets and metadata hints

    for unknown, generic, or binary files.
    """

    def extract(self, metadata: FileMetadata) -> ExtractedContent:
        metadata_hints: dict[str, Any] = {
            "tool": "fallback_extractor",
            "mime_type": metadata.mime_type,
            "size_bytes": metadata.size_bytes,
            "extension": metadata.extension,
        }

        snippet = ""
        try:
            with open(metadata.path, "rb") as f:
                header_bytes = f.read(1024)
            # Filter non-printable ASCII or replace invalid characters
            snippet = header_bytes.decode("utf-8", errors="replace")
            # Clean up null bytes for display
            snippet = snippet.replace("\x00", " ")
        except Exception as e:
            metadata_hints["read_error"] = str(e)

        text_content = (
            f"File: {metadata.path.name}\n"
            f"MIME type: {metadata.mime_type}\n"
            f"Size: {metadata.size_bytes} bytes\n"
            f"Header snippet:\n{snippet[:500]}"
        )

        return ExtractedContent(
            text_content=text_content,
            metadata_hints=metadata_hints,
        )
