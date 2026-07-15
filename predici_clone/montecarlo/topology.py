from __future__ import annotations

import numpy as np

from predici_clone.montecarlo.ensemble import Chain


def add_branch(chain: Chain, connection_point: int | None = None) -> int:
    point = chain.length // 2 if connection_point is None else int(connection_point)
    if point < 1 or point > chain.length:
        raise ValueError("connection point must lie on the chain")
    chain.branch_points.append(point)
    chain.indices["branch_count"] = chain.indices.get("branch_count", 0.0) + 1.0
    return point


def radius_of_gyration(
    chain: Chain,
    *,
    bond_length: float = 1.0,
    characteristic_ratio: float = 1.0,
) -> float:
    if bond_length <= 0 or characteristic_ratio <= 0:
        raise ValueError("bond length and characteristic ratio must be positive")
    linear_rg2 = characteristic_ratio * chain.length * bond_length**2 / 6.0
    shrink = shrinking_factor(chain)
    return float(np.sqrt(linear_rg2 * shrink))


def shrinking_factor(chain: Chain) -> float:
    if not chain.branch_points:
        return 1.0
    branch_density = len(chain.branch_points) / max(chain.length, 1)
    return float(np.clip(1.0 / (1.0 + 2.0 * np.sqrt(branch_density)), 0.1, 1.0))


def beta_scission(chain: Chain, position: int) -> tuple[Chain, Chain]:
    if position <= 0 or position >= chain.length:
        raise ValueError("scission position must be inside the chain")
    left = Chain(position, sequence=chain.sequence[:position], active=chain.active)
    right = Chain(chain.length - position, sequence=chain.sequence[position:], active=chain.active)
    left.branch_points = [point for point in chain.branch_points if point <= position]
    right.branch_points = [point - position for point in chain.branch_points if point > position]
    return left, right
