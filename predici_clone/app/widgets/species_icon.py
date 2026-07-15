from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpeciesIcon:
    kind: str
    label: str
    color: str


def color_tokens() -> dict[str, str]:
    return {
        "color.primary_curve": "#26547c",
        "color.reference_curve": "#f97316",
        "color.error": "#dc2626",
        "color.warning": "#d97706",
        "color.editable_cell": "#fef9c3",
    }


class SpeciesIconProvider:
    _icons = {
        "monomer": SpeciesIcon("monomer", "M", "#2563eb"),
        "initiator": SpeciesIcon("initiator", "I", "#7c3aed"),
        "radical": SpeciesIcon("radical", "R", "#dc2626"),
        "solvent": SpeciesIcon("solvent", "S", "#0891b2"),
        "polymer": SpeciesIcon("polymer", "P", "#16a34a"),
        "dead_polymer": SpeciesIcon("dead_polymer", "D", "#64748b"),
        "species": SpeciesIcon("species", "X", "#475569"),
        "parameter": SpeciesIcon("parameter", "k", "#9333ea"),
    }

    def icon_for(self, kind: str, *, polymer_dead: bool = False) -> SpeciesIcon:
        normalized = kind.strip().lower().replace(" ", "_") if kind else "species"
        if polymer_dead:
            normalized = "dead_polymer"
        return self._icons.get(normalized, self._icons["species"])
