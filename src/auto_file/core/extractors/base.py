"""Base definitions and data structures for file content extractors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from PIL import Image

from auto_file.core.detector import FileMetadata


@dataclass
class ExtractedContent:
    """Content extracted from a file for downstream understanding and routing.

    Attributes:
        text_content: Text parsed from documents, code, logs, or audio tags.
        image_content: PIL Image object (e.g. for photos or rendered scanned PDF pages).
        exif_date: Date string formatted as YYYY-MM-DD from EXIF or embedded tags.
        metadata_hints: Key-value dictionary containing format-specific metadata.
    """

    text_content: str | None = None
    image_content: Image.Image | None = None
    exif_date: str | None = None
    metadata_hints: dict[str, Any] = field(default_factory=dict)


class BaseExtractor(ABC):
    """Abstract base class for content extractors."""

    @abstractmethod
    def extract(self, metadata: FileMetadata) -> ExtractedContent:
        """Extract content and metadata from the target file.

        Args:
            metadata: FileMetadata instance describing the file.

        Returns:
            ExtractedContent dataclass with extracted text, image, date, or hints.
        """
        pass
