from __future__ import annotations

from dataclasses import dataclass

from predici_clone.api.project_schema import Project


@dataclass(frozen=True)
class ModelDiff:
    changed_parameters: dict[str, tuple[float | None, float | None]]
    added_reactions: tuple[str, ...]
    removed_reactions: tuple[str, ...]


def compare_projects(left: Project, right: Project) -> ModelDiff:
    names = left.generic_parameters.keys() | right.generic_parameters.keys()
    changed = {name: (left.generic_parameters.get(name), right.generic_parameters.get(name)) for name in sorted(names) if left.generic_parameters.get(name) != right.generic_parameters.get(name)}
    left_steps = {step.name for step in left.reaction_steps}
    right_steps = {step.name for step in right.reaction_steps}
    return ModelDiff(changed, tuple(sorted(right_steps - left_steps)), tuple(sorted(left_steps - right_steps)))
