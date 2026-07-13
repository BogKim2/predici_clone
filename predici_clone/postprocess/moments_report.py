from __future__ import annotations

import numpy as np
import pandas as pd

from predici_clone.core.moments import MomentReport, from_discrete_distribution


def summarize_distribution(state: np.ndarray, *, first_length: int = 0) -> MomentReport:
    return from_discrete_distribution(np.asarray(state, dtype=float)[3:], first_length=first_length)


def distribution_frame(distribution: np.ndarray, *, first_length: int = 0) -> pd.DataFrame:
    values = np.asarray(distribution, dtype=float)
    lengths = np.arange(first_length, first_length + values.size)
    total = float(np.sum(values))
    mass = lengths * values
    mass_total = float(np.sum(mass))
    return pd.DataFrame(
        {
            "chain_length": lengths,
            "concentration": values,
            "mole_fraction": values / total if total > 0 else np.zeros_like(values),
            "weight_fraction": mass / mass_total if mass_total > 0 else np.zeros_like(values),
        }
    )


def report_frame(report: MomentReport) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"metric": "M0", "value": report.m0},
            {"metric": "M1", "value": report.m1},
            {"metric": "M2", "value": report.m2},
            {"metric": "M3", "value": report.m3},
            {"metric": "Mn", "value": report.mn},
            {"metric": "Mw", "value": report.mw},
            {"metric": "Mz", "value": report.mz},
            {"metric": "PDI", "value": report.pdi},
            {"metric": "AMW", "value": report.amw},
            {"metric": "mass", "value": report.mass},
        ]
    )


def write_distribution_report(path: str, distribution: np.ndarray, *, first_length: int = 0) -> None:
    frame = distribution_frame(distribution, first_length=first_length)
    report = report_frame(from_discrete_distribution(distribution, first_length=first_length))
    writer_factory = _ExcelReportWriter if path.lower().endswith(".xlsx") else _CsvReportWriter
    with writer_factory(path) as writer:
        writer.write("distribution", frame)
        writer.write("moments", report)


class _ExcelReportWriter:
    def __init__(self, path: str) -> None:
        self.path = path
        self.writer = None

    def __enter__(self):
        self.writer = pd.ExcelWriter(self.path)
        return self

    def __exit__(self, *_exc) -> None:
        self.writer.close()

    def write(self, name: str, frame: pd.DataFrame) -> None:
        frame.to_excel(self.writer, sheet_name=name, index=False)


class _CsvReportWriter:
    def __init__(self, path: str) -> None:
        self.path = path

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> None:
        return None

    def write(self, name: str, frame: pd.DataFrame) -> None:
        suffix = "" if name == "distribution" else f".{name}"
        frame.to_csv(self.path.replace(".csv", f"{suffix}.csv"), index=False)
