"""Configuration management for DevContext."""

import os
from pathlib import Path
from typing import Any

import tomllib

# Default paths
CONFIG_DIR = Path.home() / ".config" / "devcontext"
DATA_DIR = Path.home() / ".local" / "share" / "devcontext"
CONFIG_FILE = CONFIG_DIR / "config.toml"
DB_FILE = DATA_DIR / "devcontext.db"

# Default configuration
DEFAULT_CONFIG = {
    "general": {
        "model": "llama3.1",
        "auto_start": True,
        "capture_terminal": False,
    },
    "display": {
        "color": True,
        "emoji": True,
    },
}


def ensure_dirs() -> None:
    """Ensure configuration and data directories exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """Load configuration from file, falling back to defaults."""
    ensure_dirs()

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            user_config = tomllib.load(f)
        # Merge with defaults
        config = DEFAULT_CONFIG.copy()
        for section, values in user_config.items():
            if section in config:
                config[section].update(values)
            else:
                config[section] = values
        return config

    return DEFAULT_CONFIG.copy()


def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(section, {}).get(key, default)


def get_model() -> str:
    """Get the configured Ollama model."""
    return get_config_value("general", "model", "llama3.1")


def use_emoji() -> bool:
    """Check if emoji display is enabled."""
    return get_config_value("display", "emoji", True)


def use_color() -> bool:
    """Check if color display is enabled."""
    return get_config_value("display", "color", True)
