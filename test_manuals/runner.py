from __future__ import annotations

from dataclasses import dataclass
import time

import numpy as np

from test_manuals.registry import ManualExample, examples


@dataclass(frozen=True)
class ManualResult:
    example: ManualExample
    status: str
    duration: float
    metrics: dict[str, float]
    reason: str = ""


def select_examples(*, pdf: str | None = None, feature: str | None = None, milestone: str | None = None, smoke: bool = False) -> tuple[ManualExample, ...]:
    selected = []
    for example in examples():
        if pdf and pdf.casefold() not in example.source_pdf.casefold():
            continue
        if feature and feature.casefold() != example.feature.casefold():
            continue
        if milestone and milestone.casefold() != example.milestone.casefold():
            continue
        if smoke and example.speed != "fast":
            continue
        selected.append(example)
    return tuple(selected)


def run_examples(selected: tuple[ManualExample, ...]) -> tuple[ManualResult, ...]:
    results = []
    for example in selected:
        started = time.perf_counter()
        try:
            metrics = {name: float(value) for name, value in example.run().items()}
            failures = []
            for name, (minimum, maximum) in example.expected.items():
                value = metrics.get(name, np.nan)
                if not np.isfinite(value) or minimum is not None and value < minimum or maximum is not None and value > maximum:
                    failures.append(name)
            status = "PASS" if not failures else "FAIL"
            reason = "" if not failures else f"Out of range: {', '.join(failures)}"
        except Exception as exc:
            metrics, status, reason = {}, "FAIL", f"{type(exc).__name__}: {exc}"
        results.append(ManualResult(example, status, time.perf_counter() - started, metrics, reason))
    return tuple(results)
