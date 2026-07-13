from predici_clone.api import IntegrationControl, OutputConfig, Project, ReactorConfig, Recipe
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs
from predici_clone.postprocess.parameter_estimation import (
    FittingExperiment,
    FittingProblem,
    MultiExperimentFittingProblem,
    OutputTarget,
    ParameterSpec,
    fit_generic_parameters,
    fit_multi_experiment_generic_parameters,
    sample_bayesian_posterior,
    sample_multi_experiment_bayesian_posterior,
)


def test_fit_generic_parameter_recovers_synthetic_mass_target():
    base = Project(
        reactor=ReactorConfig(kind="Batch", nmax=30),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    target_project = Project(
        reactor=base.reactor,
        kinetics=base.kinetics,
        recipe=base.recipe,
        outputs=base.outputs,
        generic_parameters={"GP_kp": base.kinetics.kp * 1.8},
    )
    target = compute_generic_outputs(SimulationEngine(target_project).run(), target_project.outputs)["mass"]
    problem = FittingProblem(
        project=base,
        parameters=(ParameterSpec("GP_kp", initial=base.kinetics.kp, lower=0.001, upper=1.0),),
        targets=(OutputTarget("mass", target, weight=100000.0),),
    )

    result = fit_generic_parameters(problem)

    assert result.success
    assert result.residual_norm < 1e-5
    assert abs(result.parameters["GP_kp"] - target_project.generic_parameters["GP_kp"]) < 1e-3
    assert result.covariance is not None
    assert result.correlation is not None
    assert result.condition_number is not None
    assert result.confidence_intervals is not None
    assert result.covariance.shape == (1, 1)
    assert "GP_kp" in result.confidence_intervals


def test_fit_multi_experiment_generic_parameter_recovers_shared_value():
    base_a = Project(
        reactor=ReactorConfig(kind="Batch", nmax=25),
        recipe=Recipe(integration=IntegrationControl(t_final=1.5, output_points=7)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    base_b = Project(
        reactor=ReactorConfig(kind="Batch", nmax=25),
        recipe=Recipe(integration=IntegrationControl(t_final=2.5, output_points=7)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    true_kp = base_a.kinetics.kp * 1.6

    def target_for(project: Project) -> float:
        case = Project(
            reactor=project.reactor,
            kinetics=project.kinetics,
            recipe=project.recipe,
            outputs=project.outputs,
            generic_parameters={"GP_kp": true_kp},
        )
        return compute_generic_outputs(SimulationEngine(case).run(), case.outputs)["mass"]

    problem = MultiExperimentFittingProblem(
        experiments=(
            FittingExperiment("short", base_a, (OutputTarget("mass", target_for(base_a), weight=100000.0),)),
            FittingExperiment("long", base_b, (OutputTarget("mass", target_for(base_b), weight=100000.0),)),
        ),
        parameters=(ParameterSpec("GP_kp", initial=base_a.kinetics.kp, lower=0.001, upper=1.0),),
    )

    result = fit_multi_experiment_generic_parameters(problem)

    assert result.success
    assert abs(result.parameters["GP_kp"] - true_kp) < 1e-3
    assert result.correlation is not None


def test_bayesian_posterior_sampling_is_bounded_and_reproducible():
    base = Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=1.2, output_points=6)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    true_kp = base.kinetics.kp * 1.25
    target_project = Project(
        reactor=base.reactor,
        kinetics=base.kinetics,
        recipe=base.recipe,
        outputs=base.outputs,
        generic_parameters={"GP_kp": true_kp},
    )
    target = compute_generic_outputs(SimulationEngine(target_project).run(), target_project.outputs)["mass"]
    problem = FittingProblem(
        project=base,
        parameters=(ParameterSpec("GP_kp", initial=base.kinetics.kp, lower=0.02, upper=0.2),),
        targets=(OutputTarget("mass", target, weight=20000.0),),
    )

    first = sample_bayesian_posterior(problem, samples=24, burn_in=8, step_scale=0.08, seed=7)
    second = sample_bayesian_posterior(problem, samples=24, burn_in=8, step_scale=0.08, seed=7)

    assert first.samples.shape == (24, 1)
    assert first.parameter_names == ("GP_kp",)
    assert 0.0 <= first.acceptance_rate <= 1.0
    assert first.credible_intervals["GP_kp"][0] <= first.posterior_mean["GP_kp"] <= first.credible_intervals["GP_kp"][1]
    assert abs(first.posterior_mean["GP_kp"] - true_kp) < 0.08
    assert first.samples.tolist() == second.samples.tolist()


def test_multi_experiment_bayesian_sampling_combines_shared_residuals():
    base_a = Project(
        reactor=ReactorConfig(kind="Batch", nmax=18),
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=5)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    base_b = Project(
        reactor=ReactorConfig(kind="Batch", nmax=18),
        recipe=Recipe(integration=IntegrationControl(t_final=1.6, output_points=5)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    true_kp = base_a.kinetics.kp * 1.2

    def target_for(project: Project) -> float:
        case = Project(
            reactor=project.reactor,
            kinetics=project.kinetics,
            recipe=project.recipe,
            outputs=project.outputs,
            generic_parameters={"GP_kp": true_kp},
        )
        return compute_generic_outputs(SimulationEngine(case).run(), case.outputs)["mass"]

    problem = MultiExperimentFittingProblem(
        experiments=(
            FittingExperiment("a", base_a, (OutputTarget("mass", target_for(base_a), weight=20000.0),)),
            FittingExperiment("b", base_b, (OutputTarget("mass", target_for(base_b), weight=20000.0),)),
        ),
        parameters=(ParameterSpec("GP_kp", initial=base_a.kinetics.kp, lower=0.02, upper=0.2),),
    )

    result = sample_multi_experiment_bayesian_posterior(problem, samples=20, burn_in=6, step_scale=0.06, seed=11)

    assert result.samples.shape == (20, 1)
    assert result.parameter_names == ("GP_kp",)
    assert 0.0 <= result.acceptance_rate <= 1.0
    assert result.credible_intervals["GP_kp"][0] <= result.posterior_mean["GP_kp"] <= result.credible_intervals["GP_kp"][1]
