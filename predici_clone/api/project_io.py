from __future__ import annotations

import json
from pathlib import Path

from predici_clone.api.project_schema import Project


def save_project(project: Project, path: str | Path) -> None:
    target = Path(path)
    target.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")


def load_project(path: str | Path) -> Project:
    source = Path(path)
    return Project.from_dict(json.loads(source.read_text(encoding="utf-8")))
