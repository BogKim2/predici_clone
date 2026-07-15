from __future__ import annotations

from collections import Counter

from predici_clone.montecarlo.ensemble import Chain, ChainEnsemble


def chain_blocks(chain: Chain) -> tuple[tuple[str, int], ...]:
    if not chain.sequence:
        return ()
    blocks: list[tuple[str, int]] = []
    current = chain.sequence[0]
    count = 1
    for unit in chain.sequence[1:]:
        if unit == current:
            count += 1
        else:
            blocks.append((current, count))
            current = unit
            count = 1
    blocks.append((current, count))
    return tuple(blocks)


def sequence_length_distribution(ensemble: ChainEnsemble) -> dict[str, dict[int, int]]:
    distributions: dict[str, Counter[int]] = {}
    for chain in ensemble.chains:
        for monomer, length in chain_blocks(chain):
            distributions.setdefault(monomer, Counter())[length] += 1
    return {monomer: dict(sorted(counts.items())) for monomer, counts in distributions.items()}


class AutomaticSequenceTracker:
    def __init__(self) -> None:
        self._blocks: dict[int, list[tuple[str, int]]] = {}

    def append(self, chain_id: int, monomer: str) -> None:
        blocks = self._blocks.setdefault(int(chain_id), [])
        if blocks and blocks[-1][0] == monomer:
            name, length = blocks[-1]
            blocks[-1] = (name, length + 1)
        else:
            blocks.append((monomer, 1))

    def merge(self, target_id: int, source_id: int) -> None:
        for monomer, length in self._blocks.pop(int(source_id), []):
            for _ in range(length):
                self.append(target_id, monomer)

    def distribution(self) -> dict[str, dict[int, int]]:
        counts: dict[str, Counter[int]] = {}
        for blocks in self._blocks.values():
            for monomer, length in blocks:
                counts.setdefault(monomer, Counter())[length] += 1
        return {monomer: dict(sorted(values.items())) for monomer, values in counts.items()}
