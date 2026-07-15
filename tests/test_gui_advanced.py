import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from predici_clone.app.main_window import MainWindow


def test_advanced_workspace_exposes_all_plan6_subsystems_and_runs_previews():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    labels = [window.advanced_tabs.tabText(index) for index in range(window.advanced_tabs.count())]
    assert labels == ["Monte Carlo", "PSD", "Emulsion", "Parameter DB", "Replay", "Copolymerization"]
    window.mc_ensemble_size.setValue(250)
    window.advanced_tabs.setCurrentIndex(0)
    window._run_advanced_preview()
    assert "250" in window.advanced_preview.text()
    window.advanced_tabs.setCurrentIndex(1)
    window._run_advanced_preview()
    assert "Mean size" in window.advanced_preview.text()
    window.close()
    app.processEvents()
