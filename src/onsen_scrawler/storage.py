import json
from pathlib import Path

from .models import Onsen


class JsonlStorage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, onsen: Onsen) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(onsen.to_dict(), ensure_ascii=False) + "\n")
