"""Filename sanitization, slug generation, and collision resolution."""

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import unicodedata


@dataclass
class ResolvedDestination:
    """Resolved file destination and duplicate status."""

    target_path: Path
    is_duplicate: bool = False


def compute_file_sha256(path: Path | str, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hex digest of a file in streaming chunks.

    Args:
        path: Path to the target file.
        chunk_size: Byte size of chunks read into memory (default: 64 KB).

    Returns:
        Hex-encoded SHA-256 checksum string.
    """
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def sanitize_slug(raw_description: str) -> str:
    """Sanitize a raw description string into a safe filename slug.

    Rules applied:
    - Normalizes unicode characters to ASCII base equivalents.
    - Converts to lowercase.
    - Replaces characters not in [a-z0-9_] with underscores.
    - Collapses consecutive underscores into a single underscore.
    - Trims leading and trailing underscores.
    - Truncates to a maximum length of 64 characters.

    Args:
        raw_description: The description or title to sanitize.

    Returns:
        A sanitized slug string (max 64 characters).
    """
    if not raw_description:
        return ""

    # Normalize unicode to ASCII (e.g. accented characters)
    text = unicodedata.normalize("NFKD", raw_description)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Lowercase
    text = text.lower()

    # Replace non-alphanumeric and non-underscore with underscore
    text = re.sub(r"[^a-z0-9_]+", "_", text)

    # Collapse consecutive underscores
    text = re.sub(r"_+", "_", text)

    # Trim leading and trailing underscores
    text = text.strip("_")

    # Truncate to max 64 characters and strip trailing underscores from truncation
    return text[:64].rstrip("_")


def resolve_target_filename(
    date_str: str,
    description: str | None = None,
    extension: str | None = None,
    destination_dir: Path | str = Path("."),
    file_sha256: str = "",
    *,
    raw_description: str | None = None,
    original_extension: str | None = None,
) -> ResolvedDestination:
    """Resolve destination filename preventing collisions and identifying duplicates.

    Constructs filename as `<destination_dir>/<date_str>_<slug><ext>`.
    If a file exists at the target path (checked case-insensitively to prevent
    destructive overwrites):
    - Reads existing file's SHA-256 in chunks.
    - If identical SHA-256: returns `ResolvedDestination(target_path=existing_path, is_duplicate=True)`.
    - If different SHA-256: loops `_1`, `_2`, ... checking existence and hashes
      until finding an unallocated path or duplicate match.

    Args:
        date_str: Formatted date string (typically YYYY-MM-DD).
        description: Description or slug seed.
        extension: File extension (e.g. '.pdf').
        destination_dir: Target directory path.
        file_sha256: SHA-256 hash of incoming file for duplicate detection.
        raw_description: Keyword alias for `description`.
        original_extension: Keyword alias for `extension`.

    Returns:
        ResolvedDestination containing target path and duplicate flag.
    """
    desc = description if description is not None else (raw_description or "")
    ext = extension if extension is not None else (original_extension or "")
    dest_dir = Path(destination_dir)

    # Normalize extension to lowercase and ensure leading dot if present
    ext_clean = ext.strip().lower()
    if ext_clean and not ext_clean.startswith("."):
        ext_clean = f".{ext_clean}"

    # Build base stem from date and sanitized slug
    slug = sanitize_slug(desc)
    if date_str and slug:
        stem = f"{date_str}_{slug}"
    elif date_str:
        stem = f"{date_str}_document"
    elif slug:
        stem = slug
    else:
        stem = "file"

    # Map existing files in destination directory (case-insensitively)
    existing_entries: dict[str, Path] = {}
    if dest_dir.is_dir():
        try:
            for entry in dest_dir.iterdir():
                existing_entries[entry.name.lower()] = entry
        except OSError:
            pass

    def _find_existing(filename: str) -> Path | None:
        existing = existing_entries.get(filename.lower())
        if existing is not None:
            return existing
        direct = dest_dir / filename
        if direct.exists():
            return direct
        return None

    # Check candidate at base stem (no collision suffix)
    candidate_name = f"{stem}{ext_clean}"
    existing_path = _find_existing(candidate_name)

    if existing_path is None:
        return ResolvedDestination(
            target_path=dest_dir / candidate_name,
            is_duplicate=False,
        )

    # Existing file found, inspect SHA-256
    try:
        existing_sha = compute_file_sha256(existing_path)
    except OSError:
        existing_sha = None

    if existing_sha and file_sha256 and existing_sha.lower() == file_sha256.lower():
        return ResolvedDestination(
            target_path=existing_path,
            is_duplicate=True,
        )

    # Different hash or unreadable: loop numbered suffixes _1, _2, ...
    counter = 1
    while True:
        candidate_name = f"{stem}_{counter}{ext_clean}"
        existing_path = _find_existing(candidate_name)

        if existing_path is None:
            return ResolvedDestination(
                target_path=dest_dir / candidate_name,
                is_duplicate=False,
            )

        try:
            existing_sha = compute_file_sha256(existing_path)
        except OSError:
            existing_sha = None

        if (
            existing_sha
            and file_sha256
            and existing_sha.lower() == file_sha256.lower()
        ):
            return ResolvedDestination(
                target_path=existing_path,
                is_duplicate=True,
            )

        counter += 1
