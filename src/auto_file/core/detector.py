"""File detector and metadata extraction module."""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import mimetypes
from pathlib import Path
import puremagic


@dataclass
class FileMetadata:
    path: Path
    mime_type: str
    extension: str
    size_bytes: int
    ctime: datetime
    mtime: datetime
    sha256: str


def detect_file_metadata(path: Path | str) -> FileMetadata:
    """Extract metadata and inspect MIME type for a filesystem path.

    Args:
        path: Path to the target file.

    Returns:
        FileMetadata dataclass instance with file attributes and SHA-256.

    Raises:
        FileNotFoundError: If the target path does not exist or is not a regular file.
    """
    path_obj = Path(path)
    if not path_obj.is_file():
        raise FileNotFoundError(f"File not found: {path_obj}")

    stat = path_obj.stat()
    size_bytes = stat.st_size
    ctime = datetime.fromtimestamp(stat.st_ctime)
    mtime = datetime.fromtimestamp(stat.st_mtime)
    extension = path_obj.suffix.lower()

    # Compute SHA-256 hash using chunked streaming
    hasher = hashlib.sha256()
    with open(path_obj, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    sha256_hex = hasher.hexdigest()

    # Determine MIME type: puremagic binary header inspection first, fallback to mimetypes
    mime_type: str | None = None
    try:
        mime_type = puremagic.from_file(str(path_obj), mime=True)
    except (puremagic.PureError, ValueError):
        mime_type = None

    if not mime_type:
        guessed, _ = mimetypes.guess_type(str(path_obj))
        mime_type = guessed

    if not mime_type:
        mime_type = "application/octet-stream"

    return FileMetadata(
        path=path_obj,
        mime_type=mime_type,
        extension=extension,
        size_bytes=size_bytes,
        ctime=ctime,
        mtime=mtime,
        sha256=sha256_hex,
    )
