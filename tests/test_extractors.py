"""Unit tests for content extractors (PDF, Image, Text, Audio & Fallback)."""

from pathlib import Path
import wave
from PIL import Image
import mutagen
import mutagen.id3
import mutagen.wave
import pytest

from auto_file.core.detector import detect_file_metadata
from auto_file.core.extractors import (
    AudioExtractor,
    BaseExtractor,
    ExtractedContent,
    FallbackExtractor,
    ImageExtractor,
    PDFExtractor,
    TextExtractor,
    get_extractor_for_tool,
)


def test_text_extractor_utf8(tmp_path: Path):
    f = tmp_path / "notes.md"
    f.write_text("# Meeting Notes\nDiscussed budget and roadmap.", encoding="utf-8")
    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("text_extractor")
    content = extractor.extract(meta)

    assert isinstance(content, ExtractedContent)
    assert content.text_content is not None
    assert "Meeting Notes" in content.text_content
    assert "budget and roadmap" in content.text_content
    assert content.metadata_hints.get("truncated") is False


def test_text_extractor_truncation(tmp_path: Path):
    f = tmp_path / "long_doc.txt"
    large_text = "A" * 12000
    f.write_text(large_text, encoding="utf-8")
    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("text_extractor")
    content = extractor.extract(meta)

    assert content.text_content is not None
    assert len(content.text_content) == 8000
    assert content.metadata_hints.get("truncated") is True
    assert content.metadata_hints.get("char_count") == 12000


def test_text_extractor_latin1(tmp_path: Path):
    f = tmp_path / "latin1.txt"
    # Write bytes that are valid ISO-8859-1 (Latin-1) but invalid UTF-8 (e.g. 0xe9 = é)
    f.write_bytes(b"Caf\xe9 au lait et cr\xe8me")
    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("text_extractor")
    content = extractor.extract(meta)

    assert content.text_content is not None
    assert "Café" in content.text_content or "Caf" in content.text_content


def test_image_extractor_basic(tmp_path: Path):
    f = tmp_path / "simple.png"
    img = Image.new("RGBA", (80, 80), color=(255, 0, 0, 255))
    img.save(f, format="PNG")

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("image_extractor")
    content = extractor.extract(meta)

    assert isinstance(content, ExtractedContent)
    assert content.image_content is not None
    assert content.image_content.mode == "RGB"
    assert content.exif_date is None
    assert content.metadata_hints.get("width") == 80
    assert content.metadata_hints.get("height") == 80


def test_image_extractor_exif_date(tmp_path: Path):
    f = tmp_path / "photo.jpg"
    img = Image.new("RGB", (100, 100), color="blue")
    exif = img.getexif()
    # EXIF tag 36867 = DateTimeOriginal
    exif[36867] = "2026:05:15 14:30:00"
    img.save(f, format="JPEG", exif=exif)

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("image_extractor")
    content = extractor.extract(meta)

    assert content.image_content is not None
    assert content.exif_date == "2026-05-15"


def test_image_extractor_scales_large_image(tmp_path: Path):
    f = tmp_path / "large_photo.jpg"
    img = Image.new("RGB", (2000, 1500), color="green")
    img.save(f, format="JPEG")

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("image_extractor")
    content = extractor.extract(meta)

    assert content.image_content is not None
    assert max(content.image_content.size) <= 1024
    assert content.metadata_hints.get("width") == 2000
    assert content.metadata_hints.get("height") == 1500


def test_pdf_extractor_with_selectable_text(tmp_path: Path):
    # Minimal valid PDF with > 50 characters of text stream
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 95 >> stream\n"
        b"BT /F1 12 Tf 100 700 Td "
        b"(This is an official invoice for payment due on 2026-04-01 with detailed items.) Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000288 00000 n \n"
        b"0000000432 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n511\n%%EOF\n"
    )
    f = tmp_path / "invoice.pdf"
    f.write_bytes(pdf_bytes)

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("pdf_extractor")
    content = extractor.extract(meta)

    assert content.text_content is not None
    assert "official invoice" in content.text_content
    assert len(content.text_content) >= 50
    assert content.image_content is None


def test_pdf_extractor_scanned_renders_page_image(tmp_path: Path):
    # PDF with no text stream (blank / scanned page simulation)
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >> endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer << /Size 4 /Root 1 0 R >>\n"
        b"startxref\n185\n%%EOF\n"
    )
    f = tmp_path / "scanned_receipt.pdf"
    f.write_bytes(pdf_bytes)

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("pdf_extractor")
    content = extractor.extract(meta)

    assert content.image_content is not None
    assert content.image_content.mode == "RGB"
    assert content.metadata_hints.get("scanned_fallback") is True


def test_audio_extractor_tags(tmp_path: Path):
    # Create a small valid WAV file and add ID3 metadata
    f = tmp_path / "sample.wav"
    with wave.open(str(f), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00\x00" * 200)

    audio = mutagen.wave.WAVE(str(f))
    audio.add_tags()
    audio.tags.add(mutagen.id3.TIT2(encoding=3, text=["Podcast Episode 12"]))
    audio.tags.add(mutagen.id3.TPE1(encoding=3, text=["Tech Talk"]))
    audio.tags.add(mutagen.id3.TALB(encoding=3, text=["Season 2"]))
    audio.tags.add(mutagen.id3.TDRC(encoding=3, text=["2026-03-10"]))
    audio.save()

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("audio_extractor")
    content = extractor.extract(meta)

    assert isinstance(content, ExtractedContent)
    assert content.text_content is not None
    assert "Podcast Episode 12" in content.text_content
    assert "Tech Talk" in content.text_content
    assert content.metadata_hints.get("title") == "Podcast Episode 12"
    assert content.metadata_hints.get("artist") == "Tech Talk"
    assert content.exif_date == "2026-03-10"


def test_fallback_extractor(tmp_path: Path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02\x03\x04SomeHeaderIdentifier\x00\xff")

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("fallback_extractor")
    content = extractor.extract(meta)

    assert isinstance(content, ExtractedContent)
    assert content.text_content is not None
    assert "SomeHeaderIdentifier" in content.text_content
    assert content.metadata_hints.get("tool") == "fallback_extractor"


def test_get_extractor_registry():
    assert isinstance(get_extractor_for_tool("pdf_extractor"), PDFExtractor)
    assert isinstance(get_extractor_for_tool("image_extractor"), ImageExtractor)
    assert isinstance(get_extractor_for_tool("text_extractor"), TextExtractor)
    assert isinstance(get_extractor_for_tool("audio_extractor"), AudioExtractor)
    assert isinstance(get_extractor_for_tool("fallback_extractor"), FallbackExtractor)
    assert isinstance(get_extractor_for_tool("fallback"), FallbackExtractor)

    with pytest.raises(ValueError, match="Unknown extractor tool"):
        get_extractor_for_tool("unknown_tool_xyz")


def test_audio_extractor_no_tags(tmp_path: Path):
    f = tmp_path / "silent.wav"
    with wave.open(str(f), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00\x00" * 100)

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("audio_extractor")
    content = extractor.extract(meta)

    assert isinstance(content, ExtractedContent)
    assert content.text_content is not None
    assert "silent.wav" in content.text_content


def test_pdf_extractor_corrupted_file(tmp_path: Path):
    f = tmp_path / "corrupted.pdf"
    f.write_bytes(b"%PDF-not-a-valid-pdf-stream")

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("pdf_extractor")
    content = extractor.extract(meta)

    assert isinstance(content, ExtractedContent)
    assert "pdf_read_error" in content.metadata_hints or "render_error" in content.metadata_hints


def test_image_extractor_corrupted_file(tmp_path: Path):
    f = tmp_path / "corrupted.jpg"
    f.write_bytes(b"not-an-image-data")

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("image_extractor")
    content = extractor.extract(meta)

    assert isinstance(content, ExtractedContent)
    assert content.image_content is None
    assert "image_open_error" in content.metadata_hints


def test_image_extractor_exif_transpose(tmp_path: Path):
    f = tmp_path / "oriented.jpg"
    # Create image of 100 wide x 200 high
    img = Image.new("RGB", (100, 200), color="purple")
    exif = img.getexif()
    # Tag 274 is Orientation. Orientation 6 = rotate 90 degrees CW (width becomes 200, height 100)
    exif[274] = 6
    img.save(f, format="JPEG", exif=exif)

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("image_extractor")
    content = extractor.extract(meta)

    assert content.image_content is not None
    # After exif_transpose, 100x200 oriented with tag 6 becomes 200x100
    assert content.image_content.size == (200, 100)


def test_text_extractor_large_bounded_read(tmp_path: Path):
    f = tmp_path / "huge.txt"
    f.write_text("Z" * 50000, encoding="utf-8")

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("text_extractor")
    content = extractor.extract(meta)

    assert content.text_content is not None
    assert len(content.text_content) == 8000
    assert content.metadata_hints.get("truncated") is True
    assert content.metadata_hints.get("char_count") >= 50000


def test_pdf_extractor_handles_closed_permits_rename(tmp_path: Path):
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >> endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer << /Size 4 /Root 1 0 R >>\n"
        b"startxref\n185\n%%EOF\n"
    )
    f = tmp_path / "scanned_to_move.pdf"
    f.write_bytes(pdf_bytes)

    meta = detect_file_metadata(f)
    extractor = get_extractor_for_tool("pdf_extractor")
    content = extractor.extract(meta)

    assert content.image_content is not None

    # Immediate move / rename to verify no lingering file descriptors are held
    dest = tmp_path / "scanned_moved.pdf"
    f.rename(dest)
    assert dest.exists()
    assert not f.exists()


