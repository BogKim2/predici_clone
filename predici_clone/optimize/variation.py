from __future__ import annotations

from collections.abc import Callable, Iterable
from itertools import product


def run_variations(parameters: dict[str, Iterable[float]], simulate: Callable[[dict[str, float]], dict[str, float]]) -> list[dict[str, object]]:
    names = tuple(parameters)
    results = []
    for combination in product(*(parameters[name] for name in names)):
        values = dict(zip(names, map(float, combination)))
        results.append({"parameters": values, "outputs": simulate(values)})
    return results
