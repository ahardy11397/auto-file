"""Plain text, markdown, CSV, JSON, and code content extractor."""

from typing import Any

from auto_file.core.detector import FileMetadata
from auto_file.core.extractors.base import BaseExtractor, ExtractedContent

MAX_TEXT_CHARACTERS = 8000
MAX_READ_BYTES = 32768


class TextExtractor(BaseExtractor):
    """Extracts text content from plain text, markdown, CSV, JSON, and source code files,

    handling encoding fallbacks, bounded initial reads (32KB), and truncating up to 8,000 characters.
    """

    def extract(self, metadata: FileMetadata) -> ExtractedContent:
        metadata_hints: dict[str, Any] = {"tool": "text_extractor"}
        text_content: str | None = None

        raw_bytes = b""
        try:
            with open(metadata.path, "rb") as f:
                raw_bytes = f.read(MAX_READ_BYTES)
        except Exception as e:
            metadata_hints["read_error"] = str(e)
            return ExtractedContent(metadata_hints=metadata_hints)

        decoded_text = ""
        encoding_used = "utf-8"
        try:
            decoded_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                decoded_text = raw_bytes.decode("latin-1")
                encoding_used = "latin-1"
            except Exception:
                decoded_text = raw_bytes.decode("utf-8", errors="replace")
                encoding_used = "utf-8-replace"

        metadata_hints["encoding"] = encoding_used
        total_chars = len(decoded_text)
        metadata_hints["char_count"] = max(total_chars, metadata.size_bytes)

        if total_chars > MAX_TEXT_CHARACTERS or metadata.size_bytes > len(raw_bytes):
            text_content = decoded_text[:MAX_TEXT_CHARACTERS]
            metadata_hints["truncated"] = True
        else:
            text_content = decoded_text
            metadata_hints["truncated"] = False

        return ExtractedContent(
            text_content=text_content,
            metadata_hints=metadata_hints,
        )
