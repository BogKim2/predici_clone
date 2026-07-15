from __future__ import annotations

from dataclasses import dataclass, field

from predici_clone.thermo.flash import FlashResult


@dataclass
class CapeCommandState:
    attributes: dict[tuple[str, str, float], float] = field(default_factory=dict)
    phase_values: dict[tuple[str, str, str], float] = field(default_factory=dict)
    flash: FlashResult | None = None
    status: str = "white"

    def co_action(self, action: str) -> int:
        if action.upper() != "PT":
            self.status = "red"
            raise ValueError(f"Unsupported CAPE action: {action}")
        self.status = "green" if self.flash is not None else "yellow"
        return 1 if self.flash is not None else 0

    def co_attribute(self, compound: str, prop: str, temperature: float) -> float:
        return float(self.attributes.get((compound, prop, float(temperature)), 0.0))

    def co_get(self, info: str, phase: str, compound: str) -> float:
        return float(self.phase_values.get((info, phase, compound), 0.0))

    def co_set(self, info: str, phase: str, compound: str, value: float) -> float:
        self.phase_values[(info, phase, compound)] = float(value)
        return float(value)
