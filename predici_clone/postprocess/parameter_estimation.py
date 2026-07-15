from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import dual_annealing, differential_evolution, least_squares

from predici_clone.api.project_schema import Project
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    initial: float
    lower: float
    upper: float
    fixed: bool = False


@dataclass(frozen=True)
class OutputTarget:
    name: str
    value: float
    weight: float = 1.0


@dataclass(frozen=True)
class FittingProblem:
    project: Project
    parameters: tuple[ParameterSpec, ...]
    targets: tuple[OutputTarget, ...]


@dataclass(frozen=True)
class FittingExperiment:
    name: str
    project: Project
    targets: tuple[OutputTarget, ...]


@dataclass(frozen=True)
class MultiExperimentFittingProblem:
    experiments: tuple[FittingExperiment, ...]
    parameters: tuple[ParameterSpec, ...]


@dataclass(frozen=True)
class FittingResult:
    success: bool
    message: str
    parameters: dict[str, float]
    residual_norm: float
    evaluations: int
    covariance: np.ndarray | None = None
    correlation: np.ndarray | None = None
    condition_number: float | None = None
    confidence_intervals: dict[str, tuple[float, float]] | None = None
    essential_directions: dict[str, dict[str, float]] | None = None


@dataclass(frozen=True)
class BayesianSampleResult:
    samples: np.ndarray
    parameter_names: tuple[str, ...]
    log_posterior: np.ndarray
    acceptance_rate: float
    posterior_mean: dict[str, float]
    credible_intervals: dict[str, tuple[float, float]]


def fit_generic_parameters(problem: FittingProblem) -> FittingResult:
    variable_specs = [spec for spec in problem.parameters if not spec.fixed]
    fixed_values = {spec.name: spec.initial for spec in problem.parameters if spec.fixed}
    x0 = np.asarray([spec.initial for spec in variable_specs], dtype=float)
    lower = np.asarray([spec.lower for spec in variable_specs], dtype=float)
    upper = np.asarray([spec.upper for spec in variable_specs], dtype=float)

    def residuals(x: np.ndarray) -> np.ndarray:
        values = {spec.name: float(value) for spec, value in zip(variable_specs, x)}
        values.update(fixed_values)
        project = _with_generic_parameters(problem.project, values)
        result = SimulationEngine(project).run()
        outputs = compute_generic_outputs(result, project.outputs)
        return np.asarray(
            [
                target.weight * (outputs.get(target.name, 0.0) - target.value)
                for target in problem.targets
            ],
            dtype=float,
        )

    if not variable_specs:
        residual = residuals(np.asarray([], dtype=float))
        return FittingResult(True, "No variable parameters", fixed_values, float(np.linalg.norm(residual)), 0)
    result = least_squares(residuals, x0=x0, bounds=(lower, upper))
    fitted = {spec.name: float(value) for spec, value in zip(variable_specs, result.x)}
    fitted.update(fixed_values)
    covariance, correlation, condition_number, confidence_intervals, essential_directions = _diagnostics(
        result.jac,
        result.fun,
        variable_specs,
        result.x,
    )
    return FittingResult(
        success=bool(result.success),
        message=str(result.message),
        parameters=fitted,
        residual_norm=float(np.linalg.norm(result.fun)),
        evaluations=int(result.nfev),
        covariance=covariance,
        correlation=correlation,
        condition_number=condition_number,
        confidence_intervals=confidence_intervals,
        essential_directions=essential_directions,
    )


def sample_bayesian_posterior(
    problem: FittingProblem,
    *,
    samples: int = 128,
    burn_in: int = 32,
    step_scale: float = 0.05,
    seed: int = 1,
) -> BayesianSampleResult:
    variable_specs = [spec for spec in problem.parameters if not spec.fixed]
    if not variable_specs:
        empty = np.empty((0, 0), dtype=float)
        return BayesianSampleResult(empty, (), np.empty(0), 0.0, {}, {})
    rng = np.random.default_rng(seed)
    current = np.asarray([spec.initial for spec in variable_specs], dtype=float)
    lower = np.asarray([spec.lower for spec in variable_specs], dtype=float)
    upper = np.asarray([spec.upper for spec in variable_specs], dtype=float)
    span = np.maximum(upper - lower, 1e-12)
    proposal_scale = np.maximum(span * float(step_scale), 1e-12)
    current_logp = _log_posterior(problem, variable_specs, current)
    kept: list[np.ndarray] = []
    kept_logp: list[float] = []
    accepted = 0
    total = int(samples + burn_in)
    for iteration in range(total):
        proposal = current + rng.normal(0.0, proposal_scale)
        proposal_logp = _log_posterior(problem, variable_specs, proposal)
        if np.isfinite(proposal_logp) and np.log(rng.uniform()) < proposal_logp - current_logp:
            current = proposal
            current_logp = proposal_logp
            accepted += 1
        if iteration >= burn_in:
            kept.append(current.copy())
            kept_logp.append(float(current_logp))
    sample_array = np.asarray(kept, dtype=float)
    names = tuple(spec.name for spec in variable_specs)
    means = np.mean(sample_array, axis=0) if sample_array.size else np.empty(0)
    lower_q = np.quantile(sample_array, 0.025, axis=0) if sample_array.size else np.empty(0)
    upper_q = np.quantile(sample_array, 0.975, axis=0) if sample_array.size else np.empty(0)
    return BayesianSampleResult(
        samples=sample_array,
        parameter_names=names,
        log_posterior=np.asarray(kept_logp, dtype=float),
        acceptance_rate=float(accepted / total) if total else 0.0,
        posterior_mean={name: float(value) for name, value in zip(names, means)},
        credible_intervals={
            name: (float(lo), float(hi))
            for name, lo, hi in zip(names, lower_q, upper_q)
        },
    )


def sample_multi_experiment_bayesian_posterior(
    problem: MultiExperimentFittingProblem,
    *,
    samples: int = 128,
    burn_in: int = 32,
    step_scale: float = 0.05,
    seed: int = 1,
) -> BayesianSampleResult:
    variable_specs = [spec for spec in problem.parameters if not spec.fixed]
    if not variable_specs:
        empty = np.empty((0, 0), dtype=float)
        return BayesianSampleResult(empty, (), np.empty(0), 0.0, {}, {})
    rng = np.random.default_rng(seed)
    current = np.asarray([spec.initial for spec in variable_specs], dtype=float)
    lower = np.asarray([spec.lower for spec in variable_specs], dtype=float)
    upper = np.asarray([spec.upper for spec in variable_specs], dtype=float)
    span = np.maximum(upper - lower, 1e-12)
    proposal_scale = np.maximum(span * float(step_scale), 1e-12)
    current_logp = _multi_experiment_log_posterior(problem, variable_specs, current)
    kept: list[np.ndarray] = []
    kept_logp: list[float] = []
    accepted = 0
    total = int(samples + burn_in)
    for iteration in range(total):
        proposal = current + rng.normal(0.0, proposal_scale)
        proposal_logp = _multi_experiment_log_posterior(problem, variable_specs, proposal)
        if np.isfinite(proposal_logp) and np.log(rng.uniform()) < proposal_logp - current_logp:
            current = proposal
            current_logp = proposal_logp
            accepted += 1
        if iteration >= burn_in:
            kept.append(current.copy())
            kept_logp.append(float(current_logp))
    sample_array = np.asarray(kept, dtype=float)
    names = tuple(spec.name for spec in variable_specs)
    means = np.mean(sample_array, axis=0) if sample_array.size else np.empty(0)
    lower_q = np.quantile(sample_array, 0.025, axis=0) if sample_array.size else np.empty(0)
    upper_q = np.quantile(sample_array, 0.975, axis=0) if sample_array.size else np.empty(0)
    return BayesianSampleResult(
        samples=sample_array,
        parameter_names=names,
        log_posterior=np.asarray(kept_logp, dtype=float),
        acceptance_rate=float(accepted / total) if total else 0.0,
        posterior_mean={name: float(value) for name, value in zip(names, means)},
        credible_intervals={
            name: (float(lo), float(hi))
            for name, lo, hi in zip(names, lower_q, upper_q)
        },
    )


def fit_multi_experiment_generic_parameters(problem: MultiExperimentFittingProblem) -> FittingResult:
    variable_specs = [spec for spec in problem.parameters if not spec.fixed]
    fixed_values = {spec.name: spec.initial for spec in problem.parameters if spec.fixed}
    x0 = np.asarray([spec.initial for spec in variable_specs], dtype=float)
    lower = np.asarray([spec.lower for spec in variable_specs], dtype=float)
    upper = np.asarray([spec.upper for spec in variable_specs], dtype=float)

    def residuals(x: np.ndarray) -> np.ndarray:
        values = {spec.name: float(value) for spec, value in zip(variable_specs, x)}
        values.update(fixed_values)
        residual_parts = []
        for experiment in problem.experiments:
            project = _with_generic_parameters(experiment.project, values)
            result = SimulationEngine(project).run()
            outputs = compute_generic_outputs(result, project.outputs)
            residual_parts.extend(
                target.weight * (outputs.get(target.name, 0.0) - target.value)
                for target in experiment.targets
            )
        return np.asarray(residual_parts, dtype=float)

    if not variable_specs:
        residual = residuals(np.asarray([], dtype=float))
        return FittingResult(True, "No variable parameters", fixed_values, float(np.linalg.norm(residual)), 0)
    result = least_squares(residuals, x0=x0, bounds=(lower, upper))
    fitted = {spec.name: float(value) for spec, value in zip(variable_specs, result.x)}
    fitted.update(fixed_values)
    covariance, correlation, condition_number, confidence_intervals, essential_directions = _diagnostics(
        result.jac,
        result.fun,
        variable_specs,
        result.x,
    )
    return FittingResult(
        success=bool(result.success),
        message=str(result.message),
        parameters=fitted,
        residual_norm=float(np.linalg.norm(result.fun)),
        evaluations=int(result.nfev),
        covariance=covariance,
        correlation=correlation,
        condition_number=condition_number,
        confidence_intervals=confidence_intervals,
        essential_directions=essential_directions,
    )


def global_search_generic_parameters(
    problem: FittingProblem,
    *,
    maxiter: int = 20,
    seed: int = 1,
    method: str = "differential_evolution",
) -> FittingResult:
    variable_specs = [spec for spec in problem.parameters if not spec.fixed]
    fixed_values = {spec.name: spec.initial for spec in problem.parameters if spec.fixed}
    bounds = [(spec.lower, spec.upper) for spec in variable_specs]

    def objective(x: np.ndarray) -> float:
        values = {spec.name: float(value) for spec, value in zip(variable_specs, x)}
        values.update(fixed_values)
        project = _with_generic_parameters(problem.project, values)
        result = SimulationEngine(project).run()
        outputs = compute_generic_outputs(result, project.outputs)
        residual = np.asarray(
            [
                target.weight * (outputs.get(target.name, 0.0) - target.value)
                for target in problem.targets
            ],
            dtype=float,
        )
        return float(np.sum(residual * residual))

    if not variable_specs:
        local = fit_generic_parameters(problem)
        return local
    if method == "differential_evolution":
        result = differential_evolution(objective, bounds=bounds, maxiter=maxiter, seed=seed, polish=False)
        evaluations = int(result.nfev)
    elif method == "dual_annealing":
        result = dual_annealing(objective, bounds=bounds, maxiter=maxiter, seed=seed, no_local_search=True)
        evaluations = int(result.nfev)
    else:
        raise ValueError(f"Unsupported global search method: {method}")
    fitted = {spec.name: float(value) for spec, value in zip(variable_specs, result.x)}
    fitted.update(fixed_values)
    return FittingResult(
        success=bool(result.success) or np.isfinite(result.fun),
        message=str(result.message),
        parameters=fitted,
        residual_norm=float(np.sqrt(result.fun)),
        evaluations=evaluations,
    )


def _with_generic_parameters(project: Project, values: dict[str, float]) -> Project:
    parameters = dict(project.generic_parameters)
    parameters.update(values)
    return Project(
        schema_version=project.schema_version,
        name=project.name,
        reactor=project.reactor,
        kinetics=project.kinetics,
        recipe=project.recipe,
        outputs=project.outputs,
        heat_balance=project.heat_balance,
        substances=list(project.substances),
        polymers=list(project.polymers),
        reaction_steps=list(project.reaction_steps),
        general_kinetic_steps=list(project.general_kinetic_steps),
        general_initial_conditions=dict(project.general_initial_conditions),
        generic_parameters=parameters,
        parameters=list(project.parameters),
        reaction_modifier_scripts=dict(project.reaction_modifier_scripts),
    )


def _log_posterior(problem: FittingProblem, variable_specs: list[ParameterSpec], values: np.ndarray) -> float:
    lower = np.asarray([spec.lower for spec in variable_specs], dtype=float)
    upper = np.asarray([spec.upper for spec in variable_specs], dtype=float)
    if np.any(values < lower) or np.any(values > upper):
        return -np.inf
    residual = _single_experiment_residual(problem, variable_specs, values)
    likelihood = -0.5 * float(np.sum(residual * residual))
    span = np.maximum(upper - lower, 1e-12)
    prior_sigma = span / 4.0
    center = np.asarray([spec.initial for spec in variable_specs], dtype=float)
    prior = -0.5 * float(np.sum(((values - center) / prior_sigma) ** 2))
    return likelihood + prior


def _single_experiment_residual(problem: FittingProblem, variable_specs: list[ParameterSpec], values: np.ndarray) -> np.ndarray:
    fixed_values = {spec.name: spec.initial for spec in problem.parameters if spec.fixed}
    parameter_values = {spec.name: float(value) for spec, value in zip(variable_specs, values)}
    parameter_values.update(fixed_values)
    project = _with_generic_parameters(problem.project, parameter_values)
    result = SimulationEngine(project).run()
    outputs = compute_generic_outputs(result, project.outputs)
    return np.asarray(
        [
            target.weight * (outputs.get(target.name, 0.0) - target.value)
            for target in problem.targets
        ],
        dtype=float,
    )


def _multi_experiment_log_posterior(problem: MultiExperimentFittingProblem, variable_specs: list[ParameterSpec], values: np.ndarray) -> float:
    lower = np.asarray([spec.lower for spec in variable_specs], dtype=float)
    upper = np.asarray([spec.upper for spec in variable_specs], dtype=float)
    if np.any(values < lower) or np.any(values > upper):
        return -np.inf
    residual = _multi_experiment_residual(problem, variable_specs, values)
    likelihood = -0.5 * float(np.sum(residual * residual))
    span = np.maximum(upper - lower, 1e-12)
    prior_sigma = span / 4.0
    center = np.asarray([spec.initial for spec in variable_specs], dtype=float)
    prior = -0.5 * float(np.sum(((values - center) / prior_sigma) ** 2))
    return likelihood + prior


def _multi_experiment_residual(problem: MultiExperimentFittingProblem, variable_specs: list[ParameterSpec], values: np.ndarray) -> np.ndarray:
    fixed_values = {spec.name: spec.initial for spec in problem.parameters if spec.fixed}
    parameter_values = {spec.name: float(value) for spec, value in zip(variable_specs, values)}
    parameter_values.update(fixed_values)
    residual_parts = []
    for experiment in problem.experiments:
        project = _with_generic_parameters(experiment.project, parameter_values)
        result = SimulationEngine(project).run()
        outputs = compute_generic_outputs(result, project.outputs)
        residual_parts.extend(
            target.weight * (outputs.get(target.name, 0.0) - target.value)
            for target in experiment.targets
        )
    return np.asarray(residual_parts, dtype=float)


def _diagnostics(
    jacobian: np.ndarray,
    residual: np.ndarray,
    specs: list[ParameterSpec],
    values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, float, dict[str, tuple[float, float]], dict[str, dict[str, float]]]:
    if not specs:
        empty = np.empty((0, 0), dtype=float)
        return empty, empty, 0.0, {}, {}
    jtj = np.asarray(jacobian, dtype=float).T @ np.asarray(jacobian, dtype=float)
    dof = max(int(residual.size - len(specs)), 1)
    residual_variance = float(np.sum(np.asarray(residual, dtype=float) ** 2) / dof)
    covariance = np.linalg.pinv(jtj) * residual_variance
    stderr = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    denominator = np.outer(stderr, stderr)
    correlation = np.divide(covariance, denominator, out=np.zeros_like(covariance), where=denominator > 0)
    condition_number = float(np.linalg.cond(jtj)) if jtj.size else 0.0
    confidence_intervals = {
        spec.name: (float(value - 1.96 * se), float(value + 1.96 * se))
        for spec, value, se in zip(specs, values, stderr)
    }
    essential_directions = _essential_directions(jtj, specs)
    return covariance, correlation, condition_number, confidence_intervals, essential_directions


def _essential_directions(matrix: np.ndarray, specs: list[ParameterSpec]) -> dict[str, dict[str, float]]:
    if matrix.size == 0:
        return {}
    values, vectors = np.linalg.eigh(np.asarray(matrix, dtype=float))
    weakest = int(np.argmin(values))
    strongest = int(np.argmax(values))
    return {
        "weakest": _direction_dict(vectors[:, weakest], specs),
        "strongest": _direction_dict(vectors[:, strongest], specs),
    }


def _direction_dict(vector: np.ndarray, specs: list[ParameterSpec]) -> dict[str, float]:
    scale = float(np.max(np.abs(vector))) if vector.size else 0.0
    normalized = vector / scale if scale > 0.0 else vector
    return {spec.name: float(value) for spec, value in zip(specs, normalized)}
