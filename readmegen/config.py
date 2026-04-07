"""Configuration loader for ReadmeGen."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "provider": None,
    "model": None,
    "style": "professional",
    "badges": True,
    "toc": True,
    "api_docs": True,
    "contributing": True,
    "license": True,
    "output": "README.md",
    "format": "md",
    "ignore": [],
}


def load_config(project_path: Path) -> dict[str, Any]:
    """Load .readmegen.yml from the project root, falling back to defaults."""
    config = dict(DEFAULT_CONFIG)

    for name in (".readmegen.yml", ".readmegen.yaml", "readmegen.yml"):
        cfg_path = project_path / name
        if cfg_path.is_file():
            try:
                user_config = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
                if isinstance(user_config, dict):
                    config.update(user_config)
            except (yaml.YAMLError, OSError):
                pass
            break

    return config
