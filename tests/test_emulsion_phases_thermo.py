import math

import numpy as np

from predici_clone.emulsion.compartment import compartmentalization_factor
from predici_clone.emulsion.partition import equilibrium_partition
from predici_clone.emulsion.smith_ewart import radical_moments, smith_ewart_steady_state
from predici_clone.kinetics.phase_steps import equilibrate_partition, precipitate
from predici_clone.reactor.phases import MultiphaseInventory, PhaseInventory
from predici_clone.thermo.flash import pt_flash
from predici_clone.thermo.peng_robinson import Compound, PengRobinsonEOS


def test_smith_ewart_without_termination_is_poisson_and_df_limits_are_physical():
    distribution = smith_ewart_steady_state(entry_rate=0.5, exit_rate=1.0, nmax=12)
    mean = radical_moments(distribution, 1)[1]
    zero_one = np.asarray([0.5, 0.5, 0.0])

    assert np.isclose(mean, 0.5, rtol=1e-5)
    assert compartmentalization_factor(zero_one) == 0.0
    assert np.isclose(compartmentalization_factor(distribution), 1.0, rtol=1e-4)


def test_three_phase_partition_and_phase_steps_conserve_amount():
    result = equilibrium_partition(10.0, water_volume=2, polymer_volume=3, droplet_volume=1, kwp=2, kdp=4)
    water = PhaseInventory("water", 2, {"M": 7})
    polymer = PhaseInventory("polymer", 3, {"M": 3})
    inventory = MultiphaseInventory(water, polymer)
    initial = inventory.total_amount("M")
    exchange = equilibrate_partition(water, polymer, "M", 2)
    solid = PhaseInventory("solid", 1, {})
    precipitate(polymer, solid, "M", 0.1)

    assert np.isclose(result.total, 10)
    assert abs(exchange.residual) < 1e-12
    assert np.isclose(inventory.total_amount("M") + solid.amounts["M"], initial)


def test_peng_robinson_pure_root_and_binary_flash_are_physical():
    methane = Compound("methane", 190.56, 4.599e6, 0.011, 0.01604)
    butane = Compound("n-butane", 425.12, 3.796e6, 0.200, 0.05812)
    eos = PengRobinsonEOS((methane, butane))
    roots = eos.compressibility_roots(300.0, 1.0e6, np.asarray([0.5, 0.5]))
    flash = pt_flash(eos, 270.0, 2.0e6, np.asarray([0.5, 0.5]))
    balance = (1.0 - flash.vapor_fraction) * flash.liquid_composition + flash.vapor_fraction * flash.vapor_composition

    assert np.all(roots > 0)
    assert 0 <= flash.vapor_fraction <= 1
    assert np.allclose(balance, [0.5, 0.5], atol=2e-5)
    assert math.isfinite(flash.vapor_density)
