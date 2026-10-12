"""Audio metadata content extractor using mutagen."""

import re
from typing import Any

from auto_file.core.detector import FileMetadata
from auto_file.core.extractors.base import BaseExtractor, ExtractedContent


def _get_tag_value(tags: Any, candidate_keys: list[str]) -> str | None:
    """Helper to retrieve string value from mutagen tags dict/object."""
    if not tags:
        return None
    for key in candidate_keys:
        if key in tags:
            val = tags[key]
            if hasattr(val, "text") and val.text:
                return str(val.text[0])
            elif isinstance(val, list) and len(val) > 0:
                return str(val[0])
            elif val is not None:
                return str(val)
    return None


class AudioExtractor(BaseExtractor):
    """Extracts audio metadata tags (title, artist, album, date/year) using mutagen."""

    def extract(self, metadata: FileMetadata) -> ExtractedContent:
        metadata_hints: dict[str, Any] = {"tool": "audio_extractor"}
        exif_date: str | None = None
        text_content: str | None = None

        try:
            import mutagen

            audio = mutagen.File(str(metadata.path))
            if audio is not None and getattr(audio, "tags", None):
                tags = audio.tags

                title = _get_tag_value(tags, ["TIT2", "title", "\xa9nam", "TITLE"])
                artist = _get_tag_value(tags, ["TPE1", "artist", "\xa9ART", "ARTIST", "albumartist"])
                album = _get_tag_value(tags, ["TALB", "album", "\xa9alb", "ALBUM"])
                raw_date = _get_tag_value(tags, ["TDRC", "TYER", "date", "\xa9day", "DATE", "year", "YEAR"])

                if title:
                    metadata_hints["title"] = title
                if artist:
                    metadata_hints["artist"] = artist
                if album:
                    metadata_hints["album"] = album
                if raw_date:
                    metadata_hints["raw_date"] = raw_date
                    m = re.search(r"(\d{4})[:\-](\d{2})[:\-](\d{2})", raw_date)
                    if m:
                        exif_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                    elif re.match(r"^\d{4}$", raw_date.strip()):
                        exif_date = f"{raw_date.strip()}-01-01"

                # Duration if available
                if hasattr(audio, "info") and hasattr(audio.info, "length"):
                    metadata_hints["duration_seconds"] = round(audio.info.length, 2)

                # Build descriptive text content for understander
                info_lines = ["Audio Track Metadata:"]
                if title:
                    info_lines.append(f"Title: {title}")
                if artist:
                    info_lines.append(f"Artist: {artist}")
                if album:
                    info_lines.append(f"Album: {album}")
                if raw_date:
                    info_lines.append(f"Date: {raw_date}")
                if "duration_seconds" in metadata_hints:
                    info_lines.append(f"Duration: {metadata_hints['duration_seconds']}s")

                text_content = "\n".join(info_lines)
            else:
                metadata_hints["tags_found"] = False
                text_content = f"Audio file: {metadata.path.name}"
        except Exception as e:
            metadata_hints["audio_extract_error"] = str(e)
            text_content = f"Audio file: {metadata.path.name}"

        return ExtractedContent(
            text_content=text_content,
            exif_date=exif_date,
            metadata_hints=metadata_hints,
        )
