from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from predici_clone.postprocess.scripted_outputs import evaluate_script_scope
from predici_clone.script.commands import ScriptCommandState, script_command_namespace


ModifierMode = Literal["replace", "multiply"]


@dataclass(frozen=True)
class ReactionRateModifier:
    parameter: str
    script_name: str
    mode: ModifierMode


@dataclass(frozen=True)
class ModifierEvaluation:
    modifier: ReactionRateModifier
    values: tuple[float, ...]


def parse_reaction_rate_modifier(expression: str) -> ReactionRateModifier:
    text = expression.strip()
    if "*File" in text:
        parameter = text.replace("*File", "").strip()
        return _modifier(parameter, "File", "multiply")
    if text.endswith(")") and "(" in text:
        parameter, suffix = text.split("(", 1)
        script_name = suffix[:-1].strip()
        return _modifier(parameter.strip(), script_name, "replace")
    raise ValueError(f"Unsupported reaction rate modifier: {expression}")


def evaluate_reaction_rate_modifier(
    modifier: ReactionRateModifier,
    *,
    scripts: dict[str, str],
    state: ScriptCommandState,
    base_value: float,
    result_count: int = 1,
) -> ModifierEvaluation:
    if modifier.script_name not in scripts:
        raise ValueError(f"Unknown modifier script: {modifier.script_name}")
    scope = evaluate_script_scope(scripts[modifier.script_name], script_command_namespace(state))
    values = _result_values(scope, result_count)
    if modifier.mode == "multiply":
        values = tuple(float(base_value) * value for value in values)
    return ModifierEvaluation(modifier=modifier, values=values)


def evaluate_modifier_expression(
    expression: str,
    *,
    scripts: dict[str, str],
    state: ScriptCommandState,
    result_count: int = 1,
) -> ModifierEvaluation:
    modifier = parse_reaction_rate_modifier(expression)
    base_value = state.parameters.get(modifier.parameter, 0.0)
    return evaluate_reaction_rate_modifier(
        modifier,
        scripts=scripts,
        state=state,
        base_value=base_value,
        result_count=result_count,
    )


def _result_values(scope: dict[str, object], result_count: int) -> tuple[float, ...]:
    if result_count <= 1:
        if "result" in scope:
            return (float(scope["result"]),)
        if "result1" in scope:
            return (float(scope["result1"]),)
        raise ValueError("Modifier script must assign result or result1")
    values = []
    for index in range(1, result_count + 1):
        name = f"result{index}"
        if name not in scope:
            raise ValueError(f"Modifier script must assign {name}")
        values.append(float(scope[name]))
    return tuple(values)


def _modifier(parameter: str, script_name: str, mode: ModifierMode) -> ReactionRateModifier:
    if not parameter:
        raise ValueError("Modifier parameter name is required")
    if not script_name:
        raise ValueError("Modifier script name is required")
    return ReactionRateModifier(parameter=parameter, script_name=script_name, mode=mode)
