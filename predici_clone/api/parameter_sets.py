from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParameterSet:
    name: str
    values: dict[str, float]
    signature: dict[str, tuple[str, float, str]]
    parent: str | None = None


class ParameterSetManager:
    def __init__(self, sets: tuple[ParameterSet, ...] = ()) -> None:
        self.sets = {item.name: item for item in sets}

    def add(self, parameter_set: ParameterSet) -> None:
        if self.sets:
            reference = next(iter(self.sets.values()))
            if parameter_set.signature != reference.signature:
                raise ValueError("parameter sets may differ only in values")
        self.sets[parameter_set.name] = parameter_set

    def duplicate(self, source: str, target: str) -> ParameterSet:
        item = self.sets[source]
        duplicate = ParameterSet(target, dict(item.values), dict(item.signature), source)
        self.sets[target] = duplicate
        return duplicate

    def activate(self, name: str, current: dict[str, float]) -> dict[str, float]:
        values = dict(current)
        values.update(self.sets[name].values)
        return values

    def diff(self, left: str, right: str) -> dict[str, tuple[float | None, float | None]]:
        a, b = self.sets[left].values, self.sets[right].values
        return {name: (a.get(name), b.get(name)) for name in sorted(a.keys() | b.keys()) if a.get(name) != b.get(name)}
