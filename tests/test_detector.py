import hashlib
from datetime import datetime
from pathlib import Path
import pytest
from auto_file.core.detector import detect_file_metadata, FileMetadata


def test_detect_text_file(tmp_path: Path):
    f = tmp_path / "sample.txt"
    f.write_text("Hello world", encoding="utf-8")
    meta = detect_file_metadata(f)
    assert isinstance(meta, FileMetadata)
    assert meta.extension == ".txt"
    assert "text" in meta.mime_type
    assert meta.size_bytes == 11
    assert len(meta.sha256) == 64
    assert isinstance(meta.ctime, datetime)
    assert isinstance(meta.mtime, datetime)
    assert meta.path == f


def test_detect_misnamed_file(tmp_path: Path):
    # PDF magic signature with .txt extension
    f = tmp_path / "fake.txt"
    f.write_bytes(b"%PDF-1.4\n%test\n")
    meta = detect_file_metadata(f)
    assert meta.mime_type == "application/pdf"
    assert meta.extension == ".txt"


def test_detect_exact_sha256(tmp_path: Path):
    f = tmp_path / "data.bin"
    content = b"deterministic test content 12345"
    f.write_bytes(content)
    expected_hash = hashlib.sha256(content).hexdigest()
    meta = detect_file_metadata(f)
    assert meta.sha256 == expected_hash
    assert meta.size_bytes == len(content)


def test_detect_uppercase_extension(tmp_path: Path):
    f = tmp_path / "DOCUMENT.TXT"
    f.write_text("uppercase extension test", encoding="utf-8")
    meta = detect_file_metadata(f)
    assert meta.extension == ".txt"


def test_detect_extensionless_file(tmp_path: Path):
    f = tmp_path / "extensionless"
    f.write_text("some notes here", encoding="utf-8")
    meta = detect_file_metadata(f)
    assert meta.extension == ""
    assert "text" in meta.mime_type


def test_detect_nonexistent_file(tmp_path: Path):
    f = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError):
        detect_file_metadata(f)


def test_detect_fallback_mimetype(tmp_path: Path):
    # Unknown binary data with .customext that neither puremagic nor mimetypes knows
    f = tmp_path / "unknown.xyzunknown"
    f.write_bytes(b"\x00\x01\x02\x03\x04")
    meta = detect_file_metadata(f)
    assert meta.mime_type == "application/octet-stream"
