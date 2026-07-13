import numpy as np

from predici_clone.api import Project, ReactorConfig, cape_open_capability, cape_open_manifest
from predici_clone.kinetics import (
    ReactionKind,
    assemble_reaction_step_rhs,
    instantiate_controlled_radical_step,
    living_polymerization_templates,
)
from predici_clone.postprocess.particle_size import particle_size_from_distribution


def test_cape_open_capability_descriptor_reports_project_reactor():
    project = Project(reactor=ReactorConfig(kind="PFR"))

    capability = cape_open_capability(project)
    manifest = cape_open_manifest(project)

    assert capability.component_name == "PrediciClone"
    assert capability.supported_reactors == ("PFR",)
    assert capability.supports_dynamic_simulation
    assert "SimulationEngine.run" in manifest["interfaces"]["unit_operation"]
    assert "not a COM registration" in capability.notes


def test_controlled_radical_templates_instantiate_raft_nmp_atrp_steps():
    templates = living_polymerization_templates()
    names = {template.name for template in templates}
    raft = instantiate_controlled_radical_step("RAFT", rate=0.02)
    nmp = instantiate_controlled_radical_step("NMP")
    atrp = instantiate_controlled_radical_step("ATRP")

    assert {"RAFT transfer", "NMP reversible capping", "ATRP activation"} <= names
    assert raft.kind == ReactionKind.CHAIN_TRANSFER_TO_AGENT
    assert nmp.rate_law.parameters == ("GP_nmp",)
    assert atrp.kind == ReactionKind.INITIATION

    distribution = np.asarray([0.0, 0.2, 0.4, 0.1])
    rhs = assemble_reaction_step_rhs(distribution, raft, {"GP_raft": 0.5})
    assert rhs.shape == distribution.shape
    assert rhs[0] > 0.0


def test_particle_size_distribution_reports_normalized_psd_and_quantiles():
    psd = particle_size_from_distribution(np.asarray([0.0, 1.0, 3.0, 1.0]), first_length=1)
    frame = psd.to_frame()
    d10, d50, d90 = psd.d10_d50_d90

    np.testing.assert_allclose(np.sum(psd.normalized), 1.0)
    assert list(frame.columns) == ["diameter", "number_density", "fraction"]
    assert d10 <= d50 <= d90
