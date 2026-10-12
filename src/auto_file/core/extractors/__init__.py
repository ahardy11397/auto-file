"""Content extractors package for Auto-File."""

from typing import Type

from auto_file.core.extractors.audio import AudioExtractor
from auto_file.core.extractors.base import BaseExtractor, ExtractedContent
from auto_file.core.extractors.fallback import FallbackExtractor
from auto_file.core.extractors.image import ImageExtractor
from auto_file.core.extractors.pdf import PDFExtractor
from auto_file.core.extractors.text import TextExtractor

_EXTRACTOR_REGISTRY: dict[str, Type[BaseExtractor]] = {
    "pdf_extractor": PDFExtractor,
    "image_extractor": ImageExtractor,
    "text_extractor": TextExtractor,
    "audio_extractor": AudioExtractor,
    "fallback_extractor": FallbackExtractor,
    "fallback": FallbackExtractor,
}


def get_extractor_for_tool(tool_name: str) -> BaseExtractor:
    """Return an instantiated extractor for the specified tool identifier.

    Args:
        tool_name: One of 'pdf_extractor', 'image_extractor', 'text_extractor',
            'audio_extractor', or 'fallback_extractor'.

    Returns:
        An instance of BaseExtractor.

    Raises:
        ValueError: If tool_name is not registered in the extractor registry.
    """
    normalized_name = tool_name.strip().lower()
    extractor_cls = _EXTRACTOR_REGISTRY.get(normalized_name)
    if extractor_cls is None:
        raise ValueError(
            f"Unknown extractor tool: '{tool_name}'. "
            f"Supported tools: {list(_EXTRACTOR_REGISTRY.keys())}"
        )
    return extractor_cls()


__all__ = [
    "BaseExtractor",
    "ExtractedContent",
    "PDFExtractor",
    "ImageExtractor",
    "TextExtractor",
    "AudioExtractor",
    "FallbackExtractor",
    "get_extractor_for_tool",
]
