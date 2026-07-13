from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module, util
from pathlib import Path


@dataclass(frozen=True)
class PackagingSmokeReport:
    spec_path: Path
    entry_script: Path
    app_name: str
    pyinstaller_available: bool
    checks: dict[str, bool]

    @property
    def success(self) -> bool:
        return all(self.checks.values())


def inspect_pyinstaller_packaging(spec_path: str | Path = "packaging/pyinstaller_predici_clone.spec") -> PackagingSmokeReport:
    spec = Path(spec_path)
    text = spec.read_text(encoding="utf-8") if spec.exists() else ""
    entry = Path("predici_clone/app/main.py")
    app_name = "PrediciClone"
    checks = {
        "spec_exists": spec.exists(),
        "entry_script_exists": entry.exists(),
        "entry_script_referenced": _entry_script_referenced(text),
        "app_name_referenced": app_name in text,
        "pyside_hiddenimport": "PySide6" in text,
        "scipy_hiddenimport": "scipy" in text,
        "matplotlib_qt_backend_hiddenimport": "matplotlib.backends.backend_qtagg" in text,
        "main_callable_importable": _main_callable_importable(),
        "entrypoint_smoke_mode": "--smoke" in entry.read_text(encoding="utf-8") if entry.exists() else False,
    }
    return PackagingSmokeReport(
        spec_path=spec,
        entry_script=entry,
        app_name=app_name,
        pyinstaller_available=util.find_spec("PyInstaller") is not None,
        checks=checks,
    )


def _main_callable_importable() -> bool:
    try:
        module = import_module("predici_clone.app.main")
    except Exception:
        return False
    return callable(getattr(module, "main", None))


def _entry_script_referenced(spec_text: str) -> bool:
    normalized = spec_text.replace("\\", "/")
    if "predici_clone/app/main.py" in normalized:
        return True
    return all(token in spec_text for token in ("predici_clone", "app", "main.py"))
