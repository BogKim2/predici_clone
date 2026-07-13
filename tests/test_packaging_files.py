from pathlib import Path

from predici_clone.api.packaging_smoke import inspect_pyinstaller_packaging


def test_pyinstaller_packaging_files_exist():
    spec = Path("packaging/pyinstaller_predici_clone.spec")
    readme = Path("packaging/README.md")

    assert spec.exists()
    assert readme.exists()
    assert "PrediciClone" in spec.read_text(encoding="utf-8")
    assert "pyinstaller" in readme.read_text(encoding="utf-8").lower()


def test_pyinstaller_packaging_smoke_report_validates_entrypoint_and_spec():
    report = inspect_pyinstaller_packaging()

    assert report.success
    assert report.app_name == "PrediciClone"
    assert report.entry_script.exists()
    assert isinstance(report.pyinstaller_available, bool)
    assert report.checks["main_callable_importable"]
