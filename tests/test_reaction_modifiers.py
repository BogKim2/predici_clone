import pytest

from predici_clone.script import ScriptCommandState, evaluate_modifier_expression, parse_reaction_rate_modifier


def test_parse_reaction_rate_modifier_supports_file_and_multiplier_forms():
    replace = parse_reaction_rate_modifier("kp(File)")
    multiply = parse_reaction_rate_modifier("kt*File")

    assert replace.parameter == "kp"
    assert replace.script_name == "File"
    assert replace.mode == "replace"
    assert multiply.parameter == "kt"
    assert multiply.script_name == "File"
    assert multiply.mode == "multiply"


def test_reaction_modifier_replace_uses_script_result():
    state = ScriptCommandState(current_concentrations={"M": 2.0}, parameters={"kp": 0.1})
    scripts = {"File": 'result = getkp("kp") + getco("M")'}

    evaluation = evaluate_modifier_expression("kp(File)", scripts=scripts, state=state)

    assert evaluation.values == (2.1,)


def test_reaction_modifier_multiplier_uses_base_parameter():
    state = ScriptCommandState(current_concentrations={"M": 3.0}, parameters={"kp": 0.2})
    scripts = {"File": 'result = getco("M")'}

    evaluation = evaluate_modifier_expression("kp*File", scripts=scripts, state=state)

    assert evaluation.values == pytest.approx((0.6,))


def test_reaction_modifier_maps_multi_result_scripts():
    state = ScriptCommandState(current_concentrations={"R": 2.0}, parameters={"kt": 0.5})
    scripts = {
        "File": """
result1 = getkp("kt") * getco("R")
result2 = getkp("kt") * 2
"""
    }

    evaluation = evaluate_modifier_expression("kt(File)", scripts=scripts, state=state, result_count=2)

    assert evaluation.values == (1.0, 1.0)
