"""Image content extractor with EXIF date parsing and scaling."""

import re
from typing import Any
from PIL import ExifTags, Image

from auto_file.core.detector import FileMetadata
from auto_file.core.extractors.base import BaseExtractor, ExtractedContent


class ImageExtractor(BaseExtractor):
    """Extracts image content, EXIF dates (DateTimeOriginal), and metadata.

    Converts image to RGB mode and scales down to max 1024x1024 for visual understanding models.
    """

    def extract(self, metadata: FileMetadata) -> ExtractedContent:
        metadata_hints: dict[str, Any] = {"tool": "image_extractor"}
        exif_date: str | None = None
        processed_img: Image.Image | None = None

        try:
            with Image.open(metadata.path) as raw_img:
                metadata_hints["width"] = raw_img.width
                metadata_hints["height"] = raw_img.height
                metadata_hints["format"] = raw_img.format or metadata.extension.lstrip(".")

                # Extract EXIF DateTimeOriginal (tag 36867 or IFD Exif)
                try:
                    exif_data = raw_img.getexif()
                    if exif_data:
                        raw_date = exif_data.get(36867)
                        if not raw_date:
                            try:
                                ifd = exif_data.get_ifd(ExifTags.IFD.Exif)
                                raw_date = ifd.get(36867) or ifd.get(36868)
                            except Exception:
                                pass
                        if not raw_date:
                            raw_date = exif_data.get(306) or exif_data.get(36868)

                        if raw_date and isinstance(raw_date, str):
                            m = re.search(r"(\d{4})[:\-](\d{2})[:\-](\d{2})", raw_date)
                            if m:
                                exif_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                                metadata_hints["raw_exif_date"] = raw_date
                except Exception as e:
                    metadata_hints["exif_error"] = str(e)

                # Convert to RGB mode (handles RGBA, P, grayscale, etc.)
                rgb_img = raw_img.convert("RGB")

                # Scale to max 1024x1024 preserving aspect ratio
                if rgb_img.width > 1024 or rgb_img.height > 1024:
                    rgb_img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

                # Copy to keep in memory once file context exits
                processed_img = rgb_img.copy()

        except Exception as e:
            metadata_hints["image_open_error"] = str(e)

        return ExtractedContent(
            image_content=processed_img,
            exif_date=exif_date,
            metadata_hints=metadata_hints,
        )
