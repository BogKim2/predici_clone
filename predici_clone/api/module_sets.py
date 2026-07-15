from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleSet:
    name: str
    enabled: dict[str, bool]


def activate_module_set(current: dict[str, bool], module_set: ModuleSet) -> dict[str, bool]:
    result = dict(current)
    unknown = set(module_set.enabled) - set(current)
    if unknown:
        raise ValueError(f"Module set contains unknown reactions: {', '.join(sorted(unknown))}")
    result.update(module_set.enabled)
    return result


def module_set_from_group(name: str, reactions: tuple[str, ...], all_reactions: tuple[str, ...]) -> ModuleSet:
    selected = set(reactions)
    return ModuleSet(name, {reaction: reaction in selected for reaction in all_reactions})
