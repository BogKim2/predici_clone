from __future__ import annotations

from dataclasses import dataclass, field

from predici_clone.montecarlo.ensemble import Chain


@dataclass
class MCIndexRegistry:
    aliases: dict[str, str] = field(
        default_factory=lambda: {
            "mass": "mass",
            "weight": "mass",
            "branches": "branch_count",
            "branch": "branch_count",
            "crosslinks": "crosslink_count",
            "crosslink": "crosslink_count",
        }
    )

    def register(self, name: str, *aliases: str) -> None:
        canonical = name.strip()
        if not canonical:
            raise ValueError("index name is required")
        self.aliases[canonical.casefold()] = canonical
        for alias in aliases:
            self.aliases[alias.casefold()] = canonical

    def resolve(self, name: str) -> str:
        key = name.strip().casefold()
        if key not in self.aliases:
            self.register(name)
        return self.aliases[key]

    def increment(self, chain: Chain, name: str, amount: float = 1.0) -> None:
        canonical = self.resolve(name)
        chain.indices[canonical] = chain.indices.get(canonical, 0.0) + float(amount)

    def merge(self, target: Chain, source: Chain) -> None:
        for name, value in source.indices.items():
            self.increment(target, name, value)
