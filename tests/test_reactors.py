import numpy as np

from predici_clone.core.moments import from_discrete_distribution
from predici_clone.kinetics import FRPScheme, SpeciesState
from predici_clone.reactor import BatchReactor, CSTRReactor, SemiBatchReactor


def test_batch_frp_generates_polymer_distribution():
    reactor = BatchReactor(
        scheme=FRPScheme(kp=0.1, kt=0.02, kd=0.04, initiator_efficiency=0.5),
        species=SpeciesState(monomer=2.0, initiator=0.2),
        nmax=60,
    )

    result = reactor.solve((0.0, 10.0), t_eval=np.linspace(0.0, 10.0, 20))

    assert result.success
    assert result.y[0, -1] < result.y[0, 0]
    report = from_discrete_distribution(result.y[3:, -1])
    assert report.m0 > 0.0
    assert report.mn > 0.0


def test_semibatch_feed_increases_volume_and_keeps_monomer_available():
    reactor = SemiBatchReactor(
        scheme=FRPScheme(kp=0.05, kt=0.02, kd=0.02),
        species=SpeciesState(monomer=0.1, initiator=0.02),
        nmax=50,
        volume=1.0,
        feed_rate=0.1,
        feed_species=SpeciesState(monomer=2.0, initiator=0.1),
    )

    result = reactor.solve((0.0, 5.0), t_eval=np.linspace(0.0, 5.0, 10))

    assert result.success
    np.testing.assert_allclose(result.y[-1, -1], 1.5, rtol=1e-5)
    assert result.y[0, -1] > result.y[0, 0]


def test_semibatch_feed_schedule_changes_volume_rate_during_integration():
    reactor = SemiBatchReactor(
        scheme=FRPScheme(kp=0.05, kt=0.02, kd=0.02),
        species=SpeciesState(monomer=0.1, initiator=0.02),
        nmax=20,
        volume=1.0,
        feed_rate=0.1,
        feed_species=SpeciesState(monomer=2.0, initiator=0.1),
        feed_rate_schedule=lambda time: 0.1 if time < 2.0 else 0.3,
    )

    assert reactor.feed_rate_at(1.0) == 0.1
    assert reactor.feed_rate_at(2.5) == 0.3

    result = reactor.solve((0.0, 4.0), t_eval=np.linspace(0.0, 4.0, 9))

    assert result.success
    np.testing.assert_allclose(result.y[-1, -1], 1.8, rtol=3e-2)


def test_cstr_approaches_positive_steady_state():
    reactor = CSTRReactor(
        scheme=FRPScheme(kp=0.06, kt=0.03, kd=0.03),
        species=SpeciesState(monomer=0.0, initiator=0.0),
        nmax=50,
        residence_time=6.0,
        feed_species=SpeciesState(monomer=2.5, initiator=0.12),
    )

    result = reactor.solve((0.0, 40.0), t_eval=np.linspace(0.0, 40.0, 80))

    assert result.success
    tail_change = np.linalg.norm(result.y[:, -1] - result.y[:, -5])
    assert tail_change < 0.2
    assert from_discrete_distribution(result.y[3:, -1]).m0 > 0.0


def test_engine_runs_cascade_and_pfr_reactors():
    from predici_clone.api import FeedStream, InitialConditions, IntegrationControl, Project, ReactorConfig, Recipe
    from predici_clone.engine import SimulationEngine

    recipe = Recipe(
        initial=InitialConditions(monomer=0.0, initiator=0.0),
        feed=FeedStream(monomer=2.0, initiator=0.1),
        integration=IntegrationControl(t_final=4.0, output_points=10),
    )
    cascade = Project(reactor=ReactorConfig(kind="Cascade", nmax=40, residence_time=5.0, stages=3), recipe=recipe)
    pfr = Project(reactor=ReactorConfig(kind="PFR", nmax=40, residence_time=5.0, axial_cells=6), recipe=recipe)

    cascade_result = SimulationEngine(cascade).run()
    pfr_result = SimulationEngine(pfr).run()

    assert cascade_result.success
    assert pfr_result.success
    assert cascade_result.final_distribution.size == 41
    assert pfr_result.final_moments.m0 > 0.0
