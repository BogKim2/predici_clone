from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class MDFData:
    times: np.ndarray
    columns: dict[str, np.ndarray]
    scales: dict[str, float]
    weights: dict[str, float]

    def statistics(self) -> dict[str, dict[str, float]]:
        return {name: {"min": float(np.nanmin(values)), "max": float(np.nanmax(values)), "variance": float(np.nanvar(values))} for name, values in self.columns.items()}


def parse_mdf(path: str | Path) -> MDFData:
    lines = [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")]
    try:
        start = lines.index("STRUCTURE")
        data_end = lines.index("END_Data")
        end = lines.index("End")
    except ValueError as exc:
        raise ValueError("MDF requires STRUCTURE, END_Data, and End markers") from exc
    if not start < data_end < end:
        raise ValueError("MDF markers are out of order")
    headers = lines[start + 1].split()
    if not headers or headers[0].casefold() != "times":
        raise ValueError("MDF first column must be times")
    rows = [[np.nan if value == "-" else float(value) for value in line.split()] for line in lines[start + 2:data_end]]
    values = np.asarray(rows, dtype=float)
    metadata = {line.split()[0].casefold(): [float(value) for value in line.split()[1:]] for line in lines[data_end + 1:end] if line.split()[0].casefold() in {"scale", "weight"}}
    columns = {name: values[:, index] for index, name in enumerate(headers[1:], start=1)}
    return MDFData(values[:, 0], columns, _metadata_map(headers[1:], metadata.get("scale"), 1.0), _metadata_map(headers[1:], metadata.get("weight"), 1.0))


def _metadata_map(names: list[str], values: list[float] | None, default: float) -> dict[str, float]:
    return {name: float(values[index]) if values and index < len(values) else default for index, name in enumerate(names)}
