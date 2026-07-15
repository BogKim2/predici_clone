import numpy as np

from predici_clone.api.module_sets import ModuleSet, activate_module_set
from predici_clone.api.parameter_sets import ParameterSet, ParameterSetManager
from predici_clone.db.parameter_db import DBFunction, DBParameter, ParameterDatabase
from predici_clone.engine.replay import Replay
from predici_clone.fitting.arrhenius import fit_arrhenius
from predici_clone.fitting.reduced_directions import analyze_reduced_directions
from predici_clone.fitting.robust import parity_data, robust_optimize
from predici_clone.optimize.variation import run_variations
from predici_clone.postprocess.dist_generator import poisson_distribution, schulz_flory


def test_parameter_database_units_sets_and_modules_round_trip(tmp_path):
    database = ParameterDatabase()
    database.add_parameter(DBParameter("DME", "PC", 53.7, "bar"))
    database.add_function(DBFunction("DME", "CP", "A+B*T", "J/mol", coefficients={"A": 10, "B": 2}))
    path = tmp_path / "db.xml"
    database.save(path)
    restored = ParameterDatabase.load(path)
    signature = {"kp": ("Arrhenius", 298.15, "batch")}
    manager = ParameterSetManager((ParameterSet("a", {"kp": 1}, signature),))
    manager.add(ParameterSet("b", {"kp": 2}, signature))

    assert np.isclose(restored.dbpar("DME", "PC", "Pa"), 5.37e6)
    assert restored.dbfunc("DME", "CP", 100) == 210
    assert manager.activate("b", {"kp": 0, "kt": 3}) == {"kp": 2, "kt": 3}
    assert activate_module_set({"r1": True, "r2": True}, ModuleSet("off", {"r2": False})) == {"r1": True, "r2": False}


def test_reduced_directions_and_arrhenius_recover_known_structure():
    jacobian = np.asarray([[1, 0, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1], [1, 1, 1, 3]], dtype=float)
    reduced = analyze_reduced_directions(jacobian)
    temperature = np.asarray([300, 320, 340, 360], dtype=float)
    rates = 2e7 * np.exp(-45000 / (8.314462618 * temperature))
    fitted = fit_arrhenius(temperature, rates)

    assert reduced.essential_dof == 3
    assert np.isclose(fitted.pre_exponential, 2e7, rtol=1e-10)
    assert np.isclose(fitted.activation_energy, 45000, rtol=1e-10)


def test_replay_outputs_distributions_and_variation_are_reusable(tmp_path):
    replay = Replay(np.asarray([0, 1]), np.asarray([[1, 2], [3, 4]]), np.asarray([[1, 2], [2, 3]]))
    path = tmp_path / "run.npz"
    replay.save(path)
    restored = Replay.load(path)
    sf = schulz_flory(10, 500)
    poisson = poisson_distribution(6, 100)
    variations = run_variations({"a": [1, 2], "b": [3, 4]}, lambda values: {"sum": sum(values.values())})

    assert restored.evaluate_output(lambda _t, state, _dist: state.sum()).tolist() == [4, 6]
    assert np.isclose(np.sum(np.arange(1, 501) * sf), 10, rtol=1e-10)
    assert np.isclose(np.sum(np.arange(1, 101) * poisson), 6, rtol=1e-10)
    assert len(variations) == 4


def test_database_clipboard_excel_and_robust_objective_surfaces(tmp_path):
    database = ParameterDatabase()
    assert database.import_clipboard("Set\tName\tDesc\tValue\tUnit\nDME\tPC\tcritical\t53.7\tbar") == 1
    assert database.export_excel(tmp_path / "db.xlsx").exists()
    result = robust_optimize(lambda values: float((values[0] - 2) ** 2), np.asarray([0.0]), np.asarray([[0.01]]), ((-5, 5),))
    parity = parity_data(np.asarray([1, 2]), np.asarray([1.1, 1.8]))

    assert abs(result.parameters[0] - 2) < 0.1
    assert parity["f2"] > 0
