"""读取集成清单，不依赖 Home Assistant 内部工具函数。"""
from __future__ import annotations

import json
from pathlib import Path

CURRENT_PATH = Path(__file__).parent


class Manifest:
    """仅暴露集成实际使用到的清单字段。"""

    def __init__(self) -> None:
        self.manifest_path = CURRENT_PATH / "manifest.json"
        self.update()

    def update(self) -> None:
        data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.domain: str = data["domain"]
        self.name: str = data["name"]
        self.version: str = data["version"]
        self.documentation: str = data.get("documentation", "")


manifest = Manifest()
