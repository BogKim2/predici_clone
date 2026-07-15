from predici_clone.postprocess.scripted_outputs import evaluate_expression
from predici_clone.script import ScriptCommandState, generate_script_template, script_command_namespace, script_function_catalog


def test_script_function_catalog_marks_implemented_and_stub_commands():
    catalog = {item.name: item for item in script_function_catalog()}

    assert catalog["getco"].implemented is True
    assert catalog["getkp"].category == "parameter"
    assert catalog["weightedmy"].implemented is True
    assert catalog["addvalue"].implemented is True


def test_script_commands_support_predici_style_getters_and_setters():
    state = ScriptCommandState(
        current_concentrations={"M": 1.5},
        initial_concentrations={"M": 2.0},
        final_concentrations={"M": 1.4},
        moments={"Mn": 100.0, "mass": 0.8},
        parameters={"kp": 0.2},
    )
    script = """
setkp("kp", getkp("kp") * 2)
result = getco("M") + getconsum("M") + getcf("M") + getmy("Mn") + gettotalmy() + getkp("kp")
"""

    value = evaluate_expression(script, script_command_namespace(state))

    assert value == 1.5 + 0.5 + 1.4 + 100.0 + 0.8 + 0.4
    assert state.parameters["kp"] == 0.4


def test_script_template_generator_creates_executable_boilerplate():
    template = generate_script_template(species=("monomer",), parameters=("kp-main",), result_names=("result1", "result2"))
    state = ScriptCommandState(current_concentrations={"monomer": 2.0}, parameters={"kp-main": 0.25})

    assert 'monomer = getco("monomer")' in template
    assert 'kp_main = getkp("kp-main")' in template
    assert "result1 = kp_main * monomer" in template
    assert evaluate_expression(template + "\nresult = result1 + result2", script_command_namespace(state)) == 0.5


def test_script_commands_support_extended_parameter_and_profile_helpers():
    state = ScriptCommandState(
        moments={"Mw": 120.0},
        weighted_moments={"Mw": 180.0},
        parameters={"kp": 0.2},
        reaction_parameters={"r1:kp": 0.3},
        time_parameters={("kp", 5.0): 0.4},
        time_position_parameters={("kp", 5.0, 0.25): 0.5},
        reactor_values={"R1": 2.5},
    )
    script = """
addvalue("acc", 1.0)
addvalue("acc", 2.0)
result = weightedmy("Mw") + getkpreac("kp", "r1") + getkpt("kp", 5.0) + getkptp("kp", 5.0, 0.25) + getuxr("R1") + getx("acc")
"""

    value = evaluate_expression(script, script_command_namespace(state))

    assert value == 180.0 + 0.3 + 0.4 + 0.5 + 2.5 + 3.0
    assert state.variables["acc"] == 3.0


def test_script_commands_interpolate_profiles_for_pde_style_helpers():
    state = ScriptCommandState(
        moments={"Mw": 120.0},
        moment_weights={"Mw": 1.5},
        parameters={"kp": 0.2},
        parameter_profiles={"kp": ((0.0, 1.0), (10.0, 3.0))},
        parameter_surfaces={"kp": ((0.0, 0.0, 1.0), (10.0, 0.0, 3.0), (0.0, 1.0, 5.0), (10.0, 1.0, 7.0))},
        reactor_profiles={"R1": ((0.0, 2.0), (1.0, 6.0))},
    )
    script = """
result = weightedmy("Mw") + getkpt("kp", 5.0) + getkptp("kp", 5.0, 0.5) + getuxr("R1", 0.25)
"""

    value = evaluate_expression(script, script_command_namespace(state))

    assert value == 180.0 + 2.0 + 4.0 + 3.0
