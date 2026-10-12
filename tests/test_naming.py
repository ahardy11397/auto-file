"""Tests for filename sanitization, slug generation, and collision resolution."""

import hashlib
from pathlib import Path

import pytest

from auto_file.core.naming import (
    ResolvedDestination,
    compute_file_sha256,
    resolve_target_filename,
    sanitize_slug,
)


def test_sanitize_slug():
    """Verify basic slug sanitization and max length truncation."""
    assert (
        sanitize_slug("Chase Bank Statement - Jan 2026!")
        == "chase_bank_statement_jan_2026"
    )
    assert len(sanitize_slug("a" * 100)) == 64


def test_sanitize_slug_variations():
    """Verify handling of unicode, consecutive delimiters, and edge cases."""
    # Accented characters normalized
    assert sanitize_slug("Résumé & CV (2026) — Final") == "resume_cv_2026_final"
    # Consecutive punctuation and spaces collapsed
    assert sanitize_slug("hello   ---   world!!!") == "hello_world"
    # Leading and trailing underscores stripped
    assert sanitize_slug("   ___sample text___   ") == "sample_text"
    # Empty and whitespace-only
    assert sanitize_slug("") == ""
    assert sanitize_slug("   ") == ""
    assert sanitize_slug("!@#$%^") == ""
    # Already clean slug
    assert sanitize_slug("invoice_12345_march") == "invoice_12345_march"


def test_resolve_no_collision(tmp_path: Path):
    """Verify resolution when destination file does not exist."""
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()

    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="Chase Statement",
        extension=".pdf",
        destination_dir=dest_dir,
        file_sha256="abc123hash",
    )
    assert isinstance(resolved, ResolvedDestination)
    assert resolved.target_path == dest_dir / "2026-01-15_chase_statement.pdf"
    assert not resolved.is_duplicate


def test_resolve_collision_different_hash(tmp_path: Path):
    """Verify collision resolution when existing file has a different hash."""
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()
    existing = dest_dir / "2026-01-15_statement.pdf"
    existing.write_bytes(b"first file content")

    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="statement",
        extension=".pdf",
        destination_dir=dest_dir,
        file_sha256="different_hash_value",
    )
    assert resolved.target_path.name == "2026-01-15_statement_1.pdf"
    assert not resolved.is_duplicate


def test_resolve_collision_identical_hash(tmp_path: Path):
    """Verify duplicate detection when existing file has identical hash."""
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()
    existing = dest_dir / "2026-01-15_statement.pdf"
    content = b"same content"
    existing.write_bytes(content)
    sha = hashlib.sha256(content).hexdigest()

    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="statement",
        extension=".pdf",
        destination_dir=dest_dir,
        file_sha256=sha,
    )
    assert resolved.target_path == existing
    assert resolved.is_duplicate


def test_resolve_multiple_collisions(tmp_path: Path):
    """Verify incrementing counter when multiple files with different hashes exist."""
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()

    (dest_dir / "2026-01-15_statement.pdf").write_bytes(b"content 0")
    (dest_dir / "2026-01-15_statement_1.pdf").write_bytes(b"content 1")
    (dest_dir / "2026-01-15_statement_2.pdf").write_bytes(b"content 2")

    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="statement",
        extension=".pdf",
        destination_dir=dest_dir,
        file_sha256="content 3 hash",
    )
    assert resolved.target_path.name == "2026-01-15_statement_3.pdf"
    assert not resolved.is_duplicate


def test_resolve_duplicate_found_at_numbered_suffix(tmp_path: Path):
    """Verify duplicate match when duplicate matches a numbered collision file."""
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()

    (dest_dir / "2026-01-15_statement.pdf").write_bytes(b"content 0")
    content_target = b"content target matches 1"
    (dest_dir / "2026-01-15_statement_1.pdf").write_bytes(content_target)
    sha = hashlib.sha256(content_target).hexdigest()

    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="statement",
        extension=".pdf",
        destination_dir=dest_dir,
        file_sha256=sha,
    )
    assert resolved.target_path == dest_dir / "2026-01-15_statement_1.pdf"
    assert resolved.is_duplicate


def test_resolve_case_insensitive_collision(tmp_path: Path):
    """Verify existing file with uppercase casing is not overwritten."""
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()
    existing_upper = dest_dir / "2026-01-15_STATEMENT.PDF"
    existing_upper.write_bytes(b"uppercase existing content")

    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="statement",
        extension=".pdf",
        destination_dir=dest_dir,
        file_sha256="different_hash",
    )
    # Must avoid collision with 2026-01-15_STATEMENT.PDF and allocate _1
    assert resolved.target_path.name == "2026-01-15_statement_1.pdf"
    assert not resolved.is_duplicate


def test_resolve_extension_normalization(tmp_path: Path):
    """Verify extensions are lowercased and leading dot is ensured."""
    dest_dir = tmp_path / "Statements"
    dest_dir.mkdir()

    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="report",
        extension="PDF",
        destination_dir=dest_dir,
        file_sha256="some_hash",
    )
    assert resolved.target_path.name == "2026-01-15_report.pdf"


def test_resolve_destination_dir_does_not_exist(tmp_path: Path):
    """Verify resolution when destination directory does not yet exist on disk."""
    dest_dir = tmp_path / "NonExistent" / "Folder"

    resolved = resolve_target_filename(
        date_str="2026-01-15",
        description="doc",
        extension=".txt",
        destination_dir=dest_dir,
        file_sha256="some_hash",
    )
    assert resolved.target_path == dest_dir / "2026-01-15_doc.txt"
    assert not resolved.is_duplicate


def test_compute_file_sha256(tmp_path: Path):
    """Verify chunked SHA-256 helper calculates accurate digest."""
    test_file = tmp_path / "data.bin"
    content = b"x" * 150000  # Multi-chunk content (>64KB)
    test_file.write_bytes(content)
    expected_sha = hashlib.sha256(content).hexdigest()

    assert compute_file_sha256(test_file) == expected_sha
