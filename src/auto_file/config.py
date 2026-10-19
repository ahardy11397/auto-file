"""Configuration management for the Auto-File System.

Handles persistent storage of user preferences, default source/destination paths,
and audit ledger locations in ~/.config/auto-file/config.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "auto-file"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_AUDIT_DB = DEFAULT_CONFIG_DIR / "audit.db"


def get_default_config_path() -> Path:
    """Return the default configuration file path."""
    return DEFAULT_CONFIG_FILE


def load_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Load configuration from disk.

    Args:
        config_path: Optional custom path to config JSON file.

    Returns:
        Dictionary of configuration options.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
    if not path.is_file():
        return {}

    try:
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return {}
        data = json.loads(content)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict[str, Any], config_path: Path | str | None = None) -> Path:
    """Save configuration dictionary to disk.

    Args:
        config: Configuration dictionary to write.
        config_path: Optional custom path to config JSON file.

    Returns:
        Path of the saved configuration file.
    """
    path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def get_config_value(key: str, default: Any = None, config_path: Path | str | None = None) -> Any:
    """Retrieve a configuration value by key.

    Args:
        key: Configuration setting name.
        default: Fallback value if setting is not present.
        config_path: Optional custom config file path.

    Returns:
        The setting value or default.
    """
    config = load_config(config_path)
    return config.get(key, default)


def set_config_value(key: str, value: Any, config_path: Path | str | None = None) -> None:
    """Store or update a configuration setting.

    Args:
        key: Configuration setting name.
        value: Value to associate with the key.
        config_path: Optional custom config file path.
    """
    config = load_config(config_path)
    config[key] = value
    save_config(config, config_path)


def get_default_dest(config_path: Path | str | None = None) -> Path | None:
    """Resolve the default destination directory from config.

    Checks keys 'dest', 'destination', 'dest_path', and 'target_root'.
    """
    config = load_config(config_path)
    for key in ("dest", "destination", "dest_path", "target_root"):
        val = config.get(key)
        if val:
            return Path(val)
    return None


def get_default_source(config_path: Path | str | None = None) -> Path | None:
    """Resolve the default source directory from config.

    Checks keys 'source', 'source_path', 'inbox'.
    """
    config = load_config(config_path)
    for key in ("source", "source_path", "inbox"):
        val = config.get(key)
        if val:
            return Path(val)
    return None


def get_structure_path(config_path: Path | str | None = None) -> Path | None:
    """Resolve the folder-structure (taxonomy) YAML file path from config.

    Checks keys 'structure', 'structure_file', and 'folder_structure'.
    Returns None when no structure file is configured (built-in defaults
    are used).
    """
    config = load_config(config_path)
    for key in ("structure", "structure_file", "folder_structure"):
        val = config.get(key)
        if val:
            return Path(val)
    return None


def get_audit_db_path(
    config_path: Path | str | None = None,
    explicit_path: Path | str | None = None,
) -> Path:
    """Resolve the active SQLite audit database path.

    Precedence:
    1. Explicit path passed as argument.
    2. Configured 'audit_db' setting in config.json.
    3. Default ~/.config/auto-file/audit.db.
    """
    if explicit_path:
        return Path(explicit_path)
    config = load_config(config_path)
    val = config.get("audit_db")
    if val:
        return Path(val)
    return DEFAULT_AUDIT_DB
