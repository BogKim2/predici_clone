import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from predici_clone.app.main_window import MainWindow
from predici_clone.app.widgets.editable_table import EditableTableWidget
from predici_clone.app.widgets.species_icon import SpeciesIconProvider, color_tokens


def test_color_tokens_separate_reference_and_error_colors():
    tokens = color_tokens()

    assert tokens["color.error"] != tokens["color.reference_curve"]
    assert tokens["color.editable_cell"] != tokens["color.error"]


def test_species_icon_provider_maps_stable_kinds():
    provider = SpeciesIconProvider()

    assert provider.icon_for("monomer").label == "M"
    assert provider.icon_for("radical").color == color_tokens()["color.error"]
    assert provider.icon_for("polymer", polymer_dead=True).label == "D"


def test_main_window_uses_editable_table_widget_for_grids():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    table_names = [
        "reaction_table",
        "reaction_pattern_catalog_table",
        "reaction_pattern_slot_table",
        "substance_table",
        "polymer_table",
        "parameter_table",
        "recipe_table",
        "fitting_parameter_table",
        "script_output_table",
        "actual_values_table",
    ]

    assert all(isinstance(getattr(window, name), EditableTableWidget) for name in table_names)
    window.close()
    app.processEvents()
