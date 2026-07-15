from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class ManualExample:
    id: str
    title: str
    source_pdf: str
    feature: str
    milestone: str
    run: Callable[[], dict[str, float]]
    expected: dict[str, tuple[float | None, float | None]]
    requires: tuple[str, ...] = ()
    speed: str = "fast"


_EXAMPLES: dict[str, ManualExample] = {}


def register(example: ManualExample) -> ManualExample:
    if example.id in _EXAMPLES:
        raise ValueError(f"Duplicate manual example id: {example.id}")
    _EXAMPLES[example.id] = example
    return example


def manual_example(**metadata):
    def decorate(function: Callable[[], dict[str, float]]):
        register(ManualExample(run=function, **metadata))
        return function
    return decorate


def examples() -> tuple[ManualExample, ...]:
    if not _EXAMPLES:
        from test_manuals.examples import catalog  # noqa: F401
    return tuple(_EXAMPLES.values())
