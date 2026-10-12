"""PDF content extractor with scanned document fallback."""

from typing import Any
from PIL import Image
import pypdf

from auto_file.core.detector import FileMetadata
from auto_file.core.extractors.base import BaseExtractor, ExtractedContent


class PDFExtractor(BaseExtractor):
    """Extracts text from PDF files using pypdf, falling back to page 1 image rendering

    for scanned documents with minimal or empty text.
    """

    def extract(self, metadata: FileMetadata) -> ExtractedContent:
        text_content: str | None = None
        image_content: Image.Image | None = None
        metadata_hints: dict[str, Any] = {"tool": "pdf_extractor"}

        raw_text = ""
        page_count = 0

        try:
            reader = pypdf.PdfReader(str(metadata.path))
            page_count = len(reader.pages)
            metadata_hints["page_count"] = page_count

            # Extract PDF document metadata if available
            if reader.metadata:
                try:
                    for k, v in reader.metadata.items():
                        if v and isinstance(v, str):
                            clean_key = str(k).lstrip("/").lower()
                            metadata_hints[clean_key] = v
                except Exception:
                    pass

            text_parts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted.strip())

            raw_text = "\n\n".join(text_parts).strip()
        except Exception as e:
            metadata_hints["pdf_read_error"] = str(e)

        # Scanned PDF detection: if text length < 50 characters, attempt page 1 image rendering
        if len(raw_text) < 50:
            if raw_text:
                text_content = raw_text

            try:
                import pypdfium2

                pdf = pypdfium2.PdfDocument(str(metadata.path))
                if len(pdf) > 0:
                    page = pdf[0]
                    pil_image = page.render(scale=2).to_pil()
                    if pil_image.mode != "RGB":
                        pil_image = pil_image.convert("RGB")
                    if pil_image.width > 1024 or pil_image.height > 1024:
                        pil_image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    image_content = pil_image
                    metadata_hints["scanned_fallback"] = True
            except Exception as e:
                metadata_hints["render_error"] = str(e)
        else:
            # Selectable text present: truncate to 8000 chars if larger
            if len(raw_text) > 8000:
                text_content = raw_text[:8000]
                metadata_hints["truncated"] = True
            else:
                text_content = raw_text
                metadata_hints["truncated"] = False

        return ExtractedContent(
            text_content=text_content,
            image_content=image_content,
            metadata_hints=metadata_hints,
        )
