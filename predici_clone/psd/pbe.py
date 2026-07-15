from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from predici_clone.psd.profile import PSDProfile


@dataclass
class PopulationBalanceModel:
    profile: PSDProfile
    solute_concentration: float = 0.0
    crystal_density: float = 1.0

    def growth_step(self, growth: np.ndarray | float, dt: float) -> PSDProfile:
        if dt < 0:
            raise ValueError("dt must be non-negative")
        rates = np.broadcast_to(np.asarray(growth, dtype=float), self.profile.number_density.shape)
        density = self.profile.number_density
        edge_flux = np.zeros(density.size + 1)
        edge_flux[1:] = np.maximum(rates, 0.0) * density
        derivative = -(edge_flux[1:] - edge_flux[:-1]) / self.profile.widths
        old_volume = self.profile.total_volume
        updated = np.maximum(density + dt * derivative, 0.0)
        self.profile = self.profile.with_density(updated)
        crystal_gain = self.crystal_density * max(self.profile.total_volume - old_volume, 0.0)
        self.solute_concentration = max(self.solute_concentration - crystal_gain, 0.0)
        if updated[-1] > max(float(updated.max()) * 1e-6, 1e-30):
            self.profile = self.profile.expanded()
        return self.profile

    def nucleation_step(self, rate: float, shape: np.ndarray, dt: float) -> PSDProfile:
        source = np.asarray(shape, dtype=float)
        if source.shape != self.profile.number_density.shape:
            raise ValueError("nucleus shape must match profile")
        normalization = float(np.sum(source * self.profile.widths))
        if normalization <= 0:
            raise ValueError("nucleus shape must have positive integral")
        updated = self.profile.number_density + dt * max(rate, 0.0) * source / normalization
        self.profile = self.profile.with_density(updated)
        return self.profile

    def breakage_step(self, breakage_rate: np.ndarray | float, dt: float) -> PSDProfile:
        old_volume = self.profile.total_volume
        rates = np.broadcast_to(np.asarray(breakage_rate, dtype=float), self.profile.number_density.shape)
        counts = self.profile.number_density * self.profile.widths
        events = np.minimum(counts, np.maximum(rates, 0.0) * counts * dt)
        new_counts = counts - events
        daughter_sizes = self.profile.centers / np.cbrt(2.0)
        _deposit_counts(new_counts, self.profile.centers, daughter_sizes, 2.0 * events)
        self.profile = self.profile.with_density(new_counts / self.profile.widths)
        self._correct_volume(old_volume)
        return self.profile

    def agglomeration_step(self, kernel: Callable[[float, float], float], dt: float) -> PSDProfile:
        old_volume = self.profile.total_volume
        counts = self.profile.number_density * self.profile.widths
        loss = np.zeros_like(counts)
        gain = np.zeros_like(counts)
        volumes = self.profile.centers**3
        for left in range(counts.size):
            for right in range(left, counts.size):
                symmetry = 0.5 if left == right else 1.0
                events = symmetry * kernel(volumes[left], volumes[right]) * counts[left] * counts[right] * dt
                events = min(events, counts[left] - loss[left], counts[right] - loss[right])
                if events <= 0:
                    continue
                loss[left] += events
                loss[right] += events
                daughter = np.cbrt(volumes[left] + volumes[right])
                _deposit_counts(gain, self.profile.centers, np.asarray([daughter]), np.asarray([events]))
        updated = np.maximum(counts - loss + gain, 0.0)
        self.profile = self.profile.with_density(updated / self.profile.widths)
        self._correct_volume(old_volume)
        return self.profile

    def residence_step(self, inlet: PSDProfile, residence_time: float, dt: float) -> PSDProfile:
        if residence_time <= 0:
            raise ValueError("residence_time must be positive")
        if not np.allclose(inlet.edges, self.profile.edges):
            raise ValueError("inlet and reactor grids must match")
        density = self.profile.number_density + dt * (inlet.number_density - self.profile.number_density) / residence_time
        self.profile = self.profile.with_density(density)
        return self.profile

    def _correct_volume(self, target: float) -> None:
        current = self.profile.total_volume
        if target > 0 and current > 0:
            self.profile = self.profile.with_density(self.profile.number_density * target / current)


def msmpr_analytic_profile(edges: np.ndarray, *, growth_rate: float, residence_time: float, nucleation_rate: float) -> PSDProfile:
    if growth_rate <= 0 or residence_time <= 0:
        raise ValueError("growth rate and residence time must be positive")
    grid = np.asarray(edges, dtype=float)
    centers = 0.5 * (grid[:-1] + grid[1:])
    density = nucleation_rate / growth_rate * np.exp(-(centers - grid[0]) / (growth_rate * residence_time))
    return PSDProfile(grid, density)


def _deposit_counts(target: np.ndarray, centers: np.ndarray, sizes: np.ndarray, counts: np.ndarray) -> None:
    for size, count in zip(np.atleast_1d(sizes), np.atleast_1d(counts)):
        index = int(np.argmin(np.abs(centers - size)))
        target[index] += count
