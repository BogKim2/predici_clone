from __future__ import annotations


def generate_script_template(
    *,
    species: tuple[str, ...] | list[str] = (),
    parameters: tuple[str, ...] | list[str] = (),
    result_names: tuple[str, ...] | list[str] = ("result",),
) -> str:
    lines: list[str] = []
    for name in species:
        variable = _safe_identifier(name)
        lines.append(f'{variable} = getco("{name}")')
    for name in parameters:
        variable = _safe_identifier(name)
        lines.append(f'{variable} = getkp("{name}")')
    if lines:
        lines.append("")
    for index, result_name in enumerate(result_names):
        target = _safe_identifier(result_name)
        seed = "0.0" if index else _default_expression(species, parameters)
        lines.append(f"{target} = {seed}")
    return "\n".join(lines)


def _default_expression(species: tuple[str, ...] | list[str], parameters: tuple[str, ...] | list[str]) -> str:
    if species and parameters:
        return f"{_safe_identifier(parameters[0])} * {_safe_identifier(species[0])}"
    if species:
        return _safe_identifier(species[0])
    if parameters:
        return _safe_identifier(parameters[0])
    return "0.0"


def _safe_identifier(name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in name.strip())
    if not cleaned:
        return "value"
    if cleaned[0].isdigit():
        cleaned = f"v_{cleaned}"
    return cleaned
