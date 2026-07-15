import pytest

from predici_clone.postprocess.scripted_outputs import evaluate_expression
from predici_clone.script import (
    ScriptCommandState,
    evaluate_modifier_expression,
    script_command_namespace,
    script_procedure_namespace,
)


def test_script_procedure_namespace_reuses_safe_function_across_output_scripts():
    procedures = script_procedure_namespace(
        """
def gel_factor(k, concentration):
    return k * concentration + 1.0
"""
    )
    state = ScriptCommandState(current_concentrations={"M": 2.0}, parameters={"kg": 0.25})
    namespace = script_command_namespace(state, procedures=procedures)

    first = evaluate_expression('result = gel_factor(getkp("kg"), getco("M"))', namespace)
    second = evaluate_expression('result = gel_factor(getkp("kg") * 2.0, getco("M"))', namespace)

    assert first == 1.5
    assert second == 2.0


def test_script_procedure_namespace_rejects_recursive_calls():
    procedures = script_procedure_namespace(
        """
def loop(value):
    return loop(value)
"""
    )

    with pytest.raises(ValueError, match="Recursive procedure calls"):
        evaluate_expression("result = loop(1.0)", procedures)


def test_reaction_modifier_and_output_script_share_procedure_library():
    procedures = script_procedure_namespace(
        """
def glass_effect(k, conversion):
    return k * (1.0 + conversion)
"""
    )
    state = ScriptCommandState(parameters={"kp": 2.0}, variables={"conversion": 0.5})
    scripts = {"File": 'result = glass_effect(getkp("kp"), getx("conversion"))'}

    modifier = evaluate_modifier_expression("kp(File)", scripts=scripts, state=state, procedures=procedures)
    output_value = evaluate_expression(
        'result = glass_effect(getkp("kp"), getx("conversion"))',
        script_command_namespace(state, procedures=procedures),
    )

    assert modifier.values == (3.0,)
    assert output_value == 3.0
