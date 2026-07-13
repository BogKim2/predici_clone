from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication

from predici_clone.app.main_window import MainWindow
from predici_clone.api import save_simulation_result


def main() -> int:
    if "--smoke" in sys.argv:
        return _smoke()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1180, 760)
    window.show()
    return app.exec()


def _smoke() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    try:
        if window.current_result is None or not window.current_result.success:
            return 2
        with tempfile.TemporaryDirectory() as directory:
            manifest = save_simulation_result(window.current_result, Path(directory) / "run_001")
            if not manifest.exists():
                return 3
        return 0
    finally:
        window.close()
        app.processEvents()


if __name__ == "__main__":
    raise SystemExit(main())
