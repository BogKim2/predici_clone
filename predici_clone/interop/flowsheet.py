from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class Flowsheet:
    units: dict[str, dict[str, object]] = field(default_factory=dict)
    streams: list[tuple[str, str]] = field(default_factory=list)

    def add_unit(self, name: str, kind: str, x: float = 0, y: float = 0) -> None:
        self.units[name] = {"kind": kind, "x": float(x), "y": float(y)}

    def connect(self, source: str, target: str) -> None:
        if source not in self.units or target not in self.units:
            raise ValueError("flowsheet endpoints must exist")
        self.streams.append((source, target))

    def export(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_text(json.dumps({"units": self.units, "streams": self.streams}, indent=2), encoding="utf-8")
        return destination
