from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import Settings, get_settings


class ConfigStore:
    def __init__(self, path: Path | None = None):
        self.path = path or Path("backend_config.json")

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text())

    def save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2))

    def apply(self) -> Settings:
        base = get_settings()
        overrides = self.load()
        for key, value in overrides.items():
            setattr(base, key.lower(), value)
        return base
