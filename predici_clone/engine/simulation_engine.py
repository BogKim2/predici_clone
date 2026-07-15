from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp

from predici_clone.api.project_schema import FeedStream, InitialConditions, Project, Recipe
from predici_clone.api.recipe_profiles import (
    apply_pre_schedule,
    effective_feed_stream,
    scheduled_additional_heat,
    scheduled_coolant_temperature,
    scheduled_feed_rate,
    scheduled_pressure,
    scheduled_residence_time,
    scheduled_temperature,
)
from predici_clone.core.adaptive import adapt_galerkin_field
from predici_clone.core.galerkin import GalerkinField
from predici_clone.core.grid import HPMesh
from predici_clone.core.moments import from_discrete_distribution
from predici_clone.kinetics import FRPScheme, SpeciesState
from predici_clone.kinetics.rate_terms import assemble_reaction_step_rhs, frp_rhs
from predici_clone.reactor import BatchReactor, CascadeReactor, CSTRReactor, PFRReactor, SemiBatchReactor, compute_lumped_energy_balance
from predici_clone.engine.galerkin_backend import project_distribution_history
from predici_clone.engine.galerkin_system import GalerkinFRPBatchSystem, GalerkinFRPCSTRSystem, GalerkinFRPSemiBatchSystem
from predici_clone.engine.simulation_result import SimulationResult
from predici_clone.script import ScriptCommandState, evaluate_modifier_expression


@dataclass(frozen=True)
class SimulationRequest:
    t_final: float | None = None
    output_points: int | None = None
    mode: str | None = None


@dataclass
class SimulationCallbacks:
    on_log: Callable[[str], None] | None = None
    on_progress: Callable[[float], None] | None = None
    on_step: Callable[[dict], None] | None = None
    should_stop: Callable[[], bool] | None = None


class SimulationEngine:
    def __init__(self, project: Project) -> None:
        self.project = project
        self._last_result: SimulationResult | None = None

    def run(self, request: SimulationRequest | None = None, callbacks: SimulationCallbacks | None = None) -> SimulationResult:
        request = request or SimulationRequest()
        callbacks = callbacks or SimulationCallbacks()
        project = self.project
        integration = project.recipe.integration
        t_final = request.t_final if request.t_final is not None else integration.t_final
        output_points = request.output_points if request.output_points is not None else integration.output_points
        t_eval = np.linspace(0.0, t_final, output_points)
        project = apply_pre_schedule(project, 0.0)

        self._log(callbacks, f"Running {project.reactor.kind} simulation to t={t_final:g}")
        if project.general_kinetic_steps:
            result = self._run_general_kinetics(project, (0.0, t_final), t_eval)
            result = self._with_actual_values_metadata(result)
            result = self._with_simulation_mode_metadata(result, project, request)
            self._emit_general_steps(callbacks, result)
            if callbacks.on_progress:
                callbacks.on_progress(1.0)
            return result
        if integration.backend == "galerkin_direct":
            result = self._run_galerkin_direct(project, (0.0, t_final), t_eval)
            if project.heat_balance.enabled:
                result = self._apply_heat_balance(project, result)
            result = self._apply_recipe_profiles(project, result, t_final)
            result = self._with_actual_values_metadata(result)
            result = self._with_simulation_mode_metadata(result, project, request)
            self._emit_steps(callbacks, result)
            if callbacks.on_progress:
                callbacks.on_progress(1.0)
            return result
        if (
            project.heat_balance.enabled
            and float(project.generic_parameters.get("temperature_dependent_kinetics", 0.0))
        ):
            result = (
                self._run_coupled_thermal_batch(project, (0.0, t_final), t_eval)
                if project.reactor.kind == "Batch"
                else self._run_coupled_thermal_process(project, (0.0, t_final), t_eval)
            )
            result = self._apply_recipe_profiles(project, result, t_final)
            result = self._with_actual_values_metadata(result)
            result = self._with_simulation_mode_metadata(result, project, request)
            self._emit_steps(callbacks, result)
            if callbacks.on_progress:
                callbacks.on_progress(1.0)
            return result
        reactor = self._build_reactor(project)
        solution = reactor.solve((0.0, t_final), t_eval=t_eval)
        if callbacks.should_stop and callbacks.should_stop():
            return self._result_from_solution(False, "Stopped", project.reactor.kind, solution)
        result = self._result_from_solution(bool(solution.success), str(solution.message), project.reactor.kind, solution)
        if project.reaction_steps:
            result = self._apply_reaction_step_postprocess(project, result)
        if integration.backend == "galerkin":
            projected = project_distribution_history(
                result.distribution_history,
                first_length=result.first_length,
                cells=integration.galerkin_cells,
                degree=integration.galerkin_degree,
            )
            result = SimulationResult(
                success=result.success,
                message=result.message,
                reactor_kind=result.reactor_kind,
                time=result.time,
                state_history=result.state_history,
                distribution_history=projected.reconstructed_history,
                first_length=result.first_length,
                metadata={
                    **result.metadata,
                    "backend": "galerkin",
                    "galerkin_dofs": projected.mesh.dofs,
                    "galerkin_cells": projected.mesh.cells,
                    "galerkin_degree": integration.galerkin_degree,
                    "galerkin_error_max": float(np.max(projected.final_error_indicators)) if projected.final_error_indicators.size else 0.0,
                    "galerkin_error_indicators": projected.final_error_indicators.tolist(),
                },
            )
        else:
            result.metadata["backend"] = "discrete"
        if project.heat_balance.enabled:
            result = self._apply_heat_balance(project, result)
        result = self._apply_recipe_profiles(project, result, t_final)
        result = self._with_actual_values_metadata(result)
        result = self._with_simulation_mode_metadata(result, project, request)
        self._emit_steps(callbacks, result)
        if callbacks.on_progress:
            callbacks.on_progress(1.0)
        return result

    def run_to_time(self, time: float, callbacks: SimulationCallbacks | None = None) -> SimulationResult:
        target = max(0.0, min(float(time), float(self.project.recipe.integration.t_final)))
        output_points = self._output_points_for_target(target)
        result = self.run(
            SimulationRequest(
                t_final=target,
                output_points=output_points,
                mode=self.project.recipe.integration.simulation_mode,
            ),
            callbacks=callbacks,
        )
        result = self._with_run_control_metadata(result, target_time=target, requested_step=False)
        self._last_result = result
        return result

    def single_step(self, callbacks: SimulationCallbacks | None = None) -> SimulationResult:
        step = self._default_step_size()
        current = 0.0 if self._last_result is None else float(self._last_result.time[-1])
        target = min(current + step, float(self.project.recipe.integration.t_final))
        result = self.run_to_time(target, callbacks=callbacks)
        result = self._with_run_control_metadata(result, target_time=target, requested_step=True)
        self._last_result = result
        return result

    def _build_reactor(self, project: Project):
        kinetics = self._effective_kinetics(project)
        initial = project.recipe.initial
        feed = effective_feed_stream(project.recipe)
        reactor = project.reactor
        scheme = FRPScheme(
            kp=kinetics.kp,
            kt=kinetics.kt,
            kd=kinetics.kd,
            initiator_efficiency=kinetics.initiator_efficiency,
        )
        species = SpeciesState(initial.monomer, initial.initiator, initial.radicals)
        feed_species = SpeciesState(feed.monomer, feed.initiator, feed.radicals)
        residence_time_schedule = None
        if project.recipe.pre_schedule:
            residence_time_schedule = lambda time, recipe=project.recipe, default=reactor.residence_time: scheduled_residence_time(recipe, time, default)
        if reactor.kind == "Batch":
            return BatchReactor(scheme=scheme, species=species, nmax=reactor.nmax)
        if reactor.kind == "Semi-batch":
            feed_rate_schedule = None
            if project.recipe.pre_schedule:
                feed_rate_schedule = lambda time, recipe=project.recipe: scheduled_feed_rate(recipe, time)
            return SemiBatchReactor(
                scheme=scheme,
                species=species,
                nmax=reactor.nmax,
                volume=reactor.volume,
                feed_rate=feed.rate,
                feed_species=feed_species,
                feed_rate_schedule=feed_rate_schedule,
            )
        if reactor.kind == "CSTR":
            return CSTRReactor(
                scheme=scheme,
                species=species,
                nmax=reactor.nmax,
                residence_time=reactor.residence_time,
                feed_species=feed_species,
                residence_time_schedule=residence_time_schedule,
            )
        if reactor.kind == "Cascade":
            return CascadeReactor(
                scheme=scheme,
                species=species,
                nmax=reactor.nmax,
                residence_time=reactor.residence_time,
                feed_species=feed_species,
                stages=reactor.stages,
                residence_time_schedule=residence_time_schedule,
            )
        if reactor.kind == "PFR":
            return PFRReactor(
                scheme=scheme,
                species=species,
                nmax=reactor.nmax,
                residence_time=reactor.residence_time,
                feed_species=feed_species,
                axial_cells=reactor.axial_cells,
                residence_time_schedule=residence_time_schedule,
            )
        raise ValueError(f"Unsupported reactor kind: {reactor.kind}")

    def _run_general_kinetics(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        species_names = self._general_species_names(project)
        species_index = {name: index for index, name in enumerate(species_names)}
        initial = np.asarray(
            [float(project.general_initial_conditions.get(name, 0.0)) for name in species_names],
            dtype=float,
        )

        def parameter_value(name: str) -> float:
            if name in project.generic_parameters:
                return float(project.generic_parameters[name])
            try:
                return float(name)
            except ValueError:
                return 0.0

        def reaction_rate(state: np.ndarray, participants) -> float:
            rate = 1.0
            nonnegative = np.maximum(state, 0.0)
            for participant in participants:
                concentration = float(nonnegative[species_index[participant.species]])
                order = participant.stoichiometry if participant.order is None else participant.order
                rate *= concentration ** float(order)
            return float(rate)

        def rhs(_time: float, state: np.ndarray) -> np.ndarray:
            derivative = np.zeros_like(state)
            for step in project.general_kinetic_steps:
                if not step.enabled:
                    continue
                forward = parameter_value(step.forward_parameter) * reaction_rate(state, step.reactants)
                backward = parameter_value(step.backward_parameter) * reaction_rate(state, step.products)
                net = forward - backward
                for participant in step.reactants:
                    derivative[species_index[participant.species]] -= participant.stoichiometry * net
                for participant in step.products:
                    derivative[species_index[participant.species]] += participant.stoichiometry * net
            return derivative

        solution = solve_ivp(
            rhs,
            t_span,
            initial,
            t_eval=t_eval,
            method=project.recipe.integration.method,
            rtol=project.recipe.integration.rtol,
            atol=project.recipe.integration.atol,
        )
        concentrations = np.maximum(solution.y, 0.0)
        concentration_history = {
            name: concentrations[index, :].tolist()
            for name, index in species_index.items()
        }
        return SimulationResult(
            success=bool(solution.success),
            message=str(solution.message),
            reactor_kind=project.reactor.kind,
            time=solution.t,
            state_history=concentrations,
            distribution_history=np.zeros((1, solution.t.size), dtype=float),
            first_length=0,
            metadata={
                "solver_status": getattr(solution, "status", None),
                "backend": "general_kinetics",
                "general_kinetics": True,
                "species_names": species_names,
                "concentration_history": concentration_history,
                "final_concentrations": {
                    name: float(concentrations[index, -1])
                    for name, index in species_index.items()
                },
                "general_kinetic_steps": len(project.general_kinetic_steps),
            },
        )

    @staticmethod
    def _general_species_names(project: Project) -> list[str]:
        names: list[str] = []
        for name in project.general_initial_conditions:
            if name not in names:
                names.append(name)
        for item in project.substances:
            name = str(item.get("name", ""))
            if name and name not in names:
                names.append(name)
        for step in project.general_kinetic_steps:
            for participant in (*step.reactants, *step.products):
                if participant.species not in names:
                    names.append(participant.species)
        return names

    def _run_galerkin_direct(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        if project.reactor.kind not in {"Batch", "Semi-batch", "CSTR", "Cascade", "PFR"}:
            raise ValueError("galerkin_direct does not support this reactor kind")
        if project.reactor.kind == "Semi-batch":
            return self._run_galerkin_direct_semibatch(project, t_span, t_eval)
        if project.reactor.kind == "CSTR":
            return self._run_galerkin_direct_cstr(project, t_span, t_eval)
        if project.reactor.kind in {"Cascade", "PFR"}:
            return self._run_galerkin_direct_cascade(project, t_span, t_eval)
        if float(project.generic_parameters.get("adaptive_galerkin", 0.0)):
            return self._run_galerkin_direct_adaptive(project, t_span, t_eval)
        integration = project.recipe.integration
        kinetics = self._effective_kinetics(project)
        initial = project.recipe.initial
        mesh = HPMesh.uniform(0.0, float(project.reactor.nmax), cells=integration.galerkin_cells, degree=integration.galerkin_degree)
        initial_field = GalerkinField.project(mesh, lambda x: np.zeros_like(np.asarray(x, dtype=float)))
        scheme = FRPScheme(
            kp=kinetics.kp,
            kt=kinetics.kt,
            kd=kinetics.kd,
            initiator_efficiency=kinetics.initiator_efficiency,
        )
        species = SpeciesState(initial.monomer, initial.initiator, initial.radicals)
        system = GalerkinFRPBatchSystem(
            mesh=mesh,
            initial_field=initial_field,
            species=species,
            scheme=scheme,
        )
        solution = system.solve(t_span, t_eval=t_eval, method=integration.method)
        lengths = np.arange(0, project.reactor.nmax + 1, dtype=float)
        distribution_history = np.empty((lengths.size, solution.y.shape[1]), dtype=float)
        for index in range(solution.y.shape[1]):
            distribution_history[:, index] = np.maximum(GalerkinField(mesh, solution.y[3:, index]).evaluate(lengths), 0.0)
        state_history = np.vstack(
            [
                solution.y[0, :],
                solution.y[1, :],
                solution.y[2, :],
                distribution_history,
            ]
        )
        return SimulationResult(
            success=bool(solution.success),
            message=str(solution.message),
            reactor_kind=project.reactor.kind,
            time=solution.t,
            state_history=state_history,
            distribution_history=distribution_history,
            first_length=0,
            metadata={
                "solver_status": getattr(solution, "status", None),
                "backend": "galerkin_direct",
                "galerkin_dofs": mesh.dofs,
                "galerkin_cells": mesh.cells,
                "galerkin_degree": integration.galerkin_degree,
                "species_coupled": True,
            },
        )

    def _run_galerkin_direct_semibatch(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        integration = project.recipe.integration
        kinetics = self._effective_kinetics(project)
        initial = project.recipe.initial
        feed = effective_feed_stream(project.recipe)
        mesh = HPMesh.uniform(0.0, float(project.reactor.nmax), cells=integration.galerkin_cells, degree=integration.galerkin_degree)
        initial_field = GalerkinField.project(mesh, lambda x: np.zeros_like(np.asarray(x, dtype=float)))
        feed_rate_schedule = None
        if project.recipe.pre_schedule:
            feed_rate_schedule = lambda time, recipe=project.recipe: scheduled_feed_rate(recipe, time)
        system = GalerkinFRPSemiBatchSystem(
            mesh=mesh,
            initial_field=initial_field,
            species=SpeciesState(initial.monomer, initial.initiator, initial.radicals),
            scheme=FRPScheme(
                kp=kinetics.kp,
                kt=kinetics.kt,
                kd=kinetics.kd,
                initiator_efficiency=kinetics.initiator_efficiency,
            ),
            volume=project.reactor.volume,
            feed_rate=feed.rate,
            feed_species=SpeciesState(feed.monomer, feed.initiator, feed.radicals),
            feed_rate_schedule=feed_rate_schedule,
        )
        solution = system.solve(t_span, t_eval=t_eval, method=integration.method)
        lengths = np.arange(0, project.reactor.nmax + 1, dtype=float)
        distribution_history = np.empty((lengths.size, solution.y.shape[1]), dtype=float)
        for index in range(solution.y.shape[1]):
            distribution_history[:, index] = np.maximum(GalerkinField(mesh, solution.y[4:, index]).evaluate(lengths), 0.0)
        state_history = np.vstack(
            [
                solution.y[0, :],
                solution.y[1, :],
                solution.y[2, :],
                distribution_history,
                solution.y[3, :],
            ]
        )
        return SimulationResult(
            success=bool(solution.success),
            message=str(solution.message),
            reactor_kind=project.reactor.kind,
            time=solution.t,
            state_history=state_history,
            distribution_history=distribution_history,
            first_length=0,
            metadata={
                "solver_status": getattr(solution, "status", None),
                "backend": "galerkin_direct",
                "galerkin_dofs": mesh.dofs,
                "galerkin_cells": mesh.cells,
                "galerkin_degree": integration.galerkin_degree,
                "species_coupled": True,
                "volume_coupled": True,
            },
        )

    def _run_galerkin_direct_cstr(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        integration = project.recipe.integration
        kinetics = self._effective_kinetics(project)
        initial = project.recipe.initial
        feed = effective_feed_stream(project.recipe)
        mesh = HPMesh.uniform(0.0, float(project.reactor.nmax), cells=integration.galerkin_cells, degree=integration.galerkin_degree)
        initial_field = GalerkinField.project(mesh, lambda x: np.zeros_like(np.asarray(x, dtype=float)))
        residence_time_schedule = None
        if project.recipe.pre_schedule:
            residence_time_schedule = lambda time, recipe=project.recipe, default=project.reactor.residence_time: scheduled_residence_time(recipe, time, default)
        solution = GalerkinFRPCSTRSystem(
            mesh=mesh,
            initial_field=initial_field,
            species=SpeciesState(initial.monomer, initial.initiator, initial.radicals),
            scheme=FRPScheme(
                kp=kinetics.kp,
                kt=kinetics.kt,
                kd=kinetics.kd,
                initiator_efficiency=kinetics.initiator_efficiency,
            ),
            residence_time=project.reactor.residence_time,
            feed_species=SpeciesState(feed.monomer, feed.initiator, feed.radicals),
            residence_time_schedule=residence_time_schedule,
        ).solve(t_span, t_eval=t_eval, method=integration.method)
        return self._galerkin_direct_result_from_solution(project, mesh, solution, coeff_start=3, extra_metadata={"residence_time_coupled": True})

    def _run_galerkin_direct_cascade(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        integration = project.recipe.integration
        kinetics = self._effective_kinetics(project)
        feed = effective_feed_stream(project.recipe)
        mesh = HPMesh.uniform(0.0, float(project.reactor.nmax), cells=integration.galerkin_cells, degree=integration.galerkin_degree)
        initial_field = GalerkinField.project(mesh, lambda x: np.zeros_like(np.asarray(x, dtype=float)))
        stages = project.reactor.stages if project.reactor.kind == "Cascade" else project.reactor.axial_cells
        stage_tau = project.reactor.residence_time / max(int(stages), 1)
        scheme = FRPScheme(
            kp=kinetics.kp,
            kt=kinetics.kt,
            kd=kinetics.kd,
            initiator_efficiency=kinetics.initiator_efficiency,
        )
        stage_species = SpeciesState(project.recipe.initial.monomer, project.recipe.initial.initiator, project.recipe.initial.radicals)
        stage_feed = SpeciesState(feed.monomer, feed.initiator, feed.radicals)
        stage_field = initial_field
        stage_solution = None
        residence_time_schedule = None
        if project.recipe.pre_schedule:
            residence_time_schedule = (
                lambda time, recipe=project.recipe, default=project.reactor.residence_time, stages=max(int(stages), 1): scheduled_residence_time(recipe, time, default) / stages
            )
        for _stage in range(max(int(stages), 1)):
            system = GalerkinFRPCSTRSystem(
                mesh=mesh,
                initial_field=stage_field,
                species=stage_species,
                scheme=scheme,
                residence_time=stage_tau,
                feed_species=stage_feed,
                residence_time_schedule=residence_time_schedule,
            )
            stage_solution = system.solve(t_span, t_eval=t_eval, method=integration.method)
            final_state = stage_solution.y[:, -1]
            stage_species = SpeciesState.from_array(final_state[:3])
            stage_feed = stage_species
            stage_field = GalerkinField(mesh, final_state[3:])
        if stage_solution is None:
            raise ValueError("Cascade requires at least one stage")
        return self._galerkin_direct_result_from_solution(
            project,
            mesh,
            stage_solution,
            coeff_start=3,
            extra_metadata={"residence_time_coupled": True, "galerkin_direct_stages": int(stages)},
        )

    def _galerkin_direct_result_from_solution(
        self,
        project: Project,
        mesh: HPMesh,
        solution,
        *,
        coeff_start: int,
        extra_metadata: dict[str, object] | None = None,
    ) -> SimulationResult:
        lengths = np.arange(0, project.reactor.nmax + 1, dtype=float)
        distribution_history = np.empty((lengths.size, solution.y.shape[1]), dtype=float)
        for index in range(solution.y.shape[1]):
            distribution_history[:, index] = np.maximum(GalerkinField(mesh, solution.y[coeff_start:, index]).evaluate(lengths), 0.0)
        state_history = np.vstack(
            [
                solution.y[0, :],
                solution.y[1, :],
                solution.y[2, :],
                distribution_history,
            ]
        )
        return SimulationResult(
            success=bool(solution.success),
            message=str(solution.message),
            reactor_kind=project.reactor.kind,
            time=solution.t,
            state_history=state_history,
            distribution_history=distribution_history,
            first_length=0,
            metadata={
                "solver_status": getattr(solution, "status", None),
                "backend": "galerkin_direct",
                "galerkin_dofs": mesh.dofs,
                "galerkin_cells": mesh.cells,
                "galerkin_degree": project.recipe.integration.galerkin_degree,
                "species_coupled": True,
                **(extra_metadata or {}),
            },
        )

    def _run_coupled_thermal_batch(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        kinetics = self._effective_kinetics(project)
        heat = project.heat_balance
        nmax = project.reactor.nmax
        initial = project.recipe.initial
        y0 = np.concatenate(
            [
                np.asarray([initial.monomer, initial.initiator, initial.radicals], dtype=float),
                np.zeros(nmax + 1, dtype=float),
                [float(heat.initial_feed_temp)],
            ]
        )
        capacity = max(float(heat.heat_capacity) * float(heat.mass_holdup), 1e-12)
        ua = float(heat.heat_transfer) * float(heat.area) if heat.use_heat_exchanger else 0.0
        reference_temperature = float(project.generic_parameters.get("reference_temperature", heat.initial_feed_temp))
        activation_energy = float(project.generic_parameters.get("activation_energy", 0.0))
        gas_constant = float(project.generic_parameters.get("gas_constant", 8.314462618))
        reaction_enthalpy = float(project.generic_parameters.get("reaction_enthalpy", 0.0))
        coolant_default = (
            heat.initial_feed_temp
            if heat.coolant_temperature == 298.15 and heat.initial_feed_temp != 298.15
            else heat.coolant_temperature
        )

        def thermal_factor(temperature: float) -> float:
            if activation_energy == 0.0:
                return 1.0
            safe_temperature = max(float(temperature), 1e-9)
            safe_reference = max(reference_temperature, 1e-9)
            exponent = activation_energy / gas_constant * (1.0 / safe_reference - 1.0 / safe_temperature)
            return float(np.exp(np.clip(exponent, -50.0, 50.0)))

        def rhs(t: float, state: np.ndarray) -> np.ndarray:
            temperature = float(state[-1])
            factor = thermal_factor(temperature)
            scheme = FRPScheme(
                kp=kinetics.kp * factor,
                kt=kinetics.kt * factor,
                kd=kinetics.kd * factor,
                initiator_efficiency=kinetics.initiator_efficiency,
            )
            chemistry_rhs = frp_rhs(t, state[:-1], scheme)
            monomer_consumption_rate = max(-float(chemistry_rhs[0]), 0.0)
            generated_heat_rate = -reaction_enthalpy * monomer_consumption_rate
            coolant = scheduled_coolant_temperature(project.recipe, t, coolant_default)
            additional_heat = scheduled_additional_heat(project.recipe, t, heat.additional_heat)
            exchanger_duty = ua * (temperature - coolant)
            d_temperature = (generated_heat_rate + additional_heat - exchanger_duty) / capacity
            return np.concatenate([chemistry_rhs, [d_temperature]])

        solution = solve_ivp(
            rhs,
            t_span,
            y0,
            t_eval=t_eval,
            method=project.recipe.integration.method,
            rtol=project.recipe.integration.rtol,
            atol=project.recipe.integration.atol,
        )
        temperature_history = solution.y[-1, :]
        chemistry_history = solution.y[:-1, :]
        distribution_history = chemistry_history[3:, :]
        coolant_history = [
            scheduled_coolant_temperature(project.recipe, float(time), coolant_default)
            for time in solution.t
        ]
        additional_heat_history = [
            scheduled_additional_heat(project.recipe, float(time), heat.additional_heat)
            for time in solution.t
        ]
        heat_duty = [
            ua * (float(temperature) - float(coolant))
            for temperature, coolant in zip(temperature_history, coolant_history)
        ]
        return SimulationResult(
            success=bool(solution.success),
            message=str(solution.message),
            reactor_kind=project.reactor.kind,
            time=solution.t,
            state_history=chemistry_history,
            distribution_history=distribution_history,
            first_length=0,
            metadata={
                "solver_status": getattr(solution, "status", None),
                "backend": "discrete",
                "heat_balance": "coupled_thermal_rhs",
                "thermal_coupled": True,
                "temperature_dependent_kinetics": True,
                "activation_energy": activation_energy,
                "reference_temperature": reference_temperature,
                "temperature_history": temperature_history.tolist(),
                "heat_duty_history": heat_duty,
                "coolant_temperature_history": coolant_history,
                "additional_heat_history": additional_heat_history,
                "final_temperature": float(temperature_history[-1]),
                "final_heat_duty": float(heat_duty[-1]),
                "final_coolant_temperature": float(coolant_history[-1]),
                "final_additional_heat": float(additional_heat_history[-1]),
            },
        )

    def _run_coupled_thermal_process(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        if project.reactor.kind == "Semi-batch":
            return self._run_coupled_thermal_semibatch(project, t_span, t_eval)
        if project.reactor.kind == "CSTR":
            return self._run_coupled_thermal_cstr(project, t_span, t_eval)
        if project.reactor.kind in {"Cascade", "PFR"}:
            return self._run_coupled_thermal_cascade(project, t_span, t_eval)
        raise ValueError(f"Unsupported thermal reactor kind: {project.reactor.kind}")

    def _run_coupled_thermal_semibatch(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        heat = project.heat_balance
        initial = project.recipe.initial
        feed = effective_feed_stream(project.recipe)
        nmax = project.reactor.nmax
        y0 = np.concatenate(
            [
                np.asarray([initial.monomer, initial.initiator, initial.radicals], dtype=float),
                np.zeros(nmax + 1, dtype=float),
                [float(project.reactor.volume), float(heat.initial_feed_temp)],
            ]
        )
        feed_species = SpeciesState(feed.monomer, feed.initiator, feed.radicals)

        def chemistry_rhs(t: float, chemistry_state: np.ndarray, scheme: FRPScheme) -> np.ndarray:
            dydt = np.zeros_like(chemistry_state, dtype=float)
            volume = max(float(chemistry_state[-1]), 1e-14)
            feed_rate = scheduled_feed_rate(project.recipe, t) if project.recipe.pre_schedule else feed.rate
            dilution = max(float(feed_rate), 0.0) / volume
            feed_vector = np.concatenate([feed_species.as_array(), np.zeros(nmax + 1)])
            dydt[:-1] = frp_rhs(t, chemistry_state[:-1], scheme) + dilution * (feed_vector - chemistry_state[:-1])
            dydt[-1] = max(float(feed_rate), 0.0)
            return dydt

        solution = self._solve_thermal_augmented(project, t_span, t_eval, y0, chemistry_rhs)
        return self._thermal_augmented_result(project, solution, chemistry_size=nmax + 5, distribution_slice=slice(3, 3 + nmax + 1))

    def _run_coupled_thermal_cstr(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        heat = project.heat_balance
        initial = project.recipe.initial
        feed = effective_feed_stream(project.recipe)
        nmax = project.reactor.nmax
        y0 = np.concatenate(
            [
                np.asarray([initial.monomer, initial.initiator, initial.radicals], dtype=float),
                np.zeros(nmax + 1, dtype=float),
                [float(heat.initial_feed_temp)],
            ]
        )
        feed_vector = np.concatenate([SpeciesState(feed.monomer, feed.initiator, feed.radicals).as_array(), np.zeros(nmax + 1)])

        def chemistry_rhs(t: float, chemistry_state: np.ndarray, scheme: FRPScheme) -> np.ndarray:
            residence_time = scheduled_residence_time(project.recipe, t, project.reactor.residence_time) if project.recipe.pre_schedule else project.reactor.residence_time
            return frp_rhs(t, chemistry_state, scheme) + (feed_vector - chemistry_state) / max(float(residence_time), 1e-12)

        solution = self._solve_thermal_augmented(project, t_span, t_eval, y0, chemistry_rhs)
        return self._thermal_augmented_result(project, solution, chemistry_size=nmax + 4, distribution_slice=slice(3, 3 + nmax + 1))

    def _run_coupled_thermal_cascade(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        stages = project.reactor.stages if project.reactor.kind == "Cascade" else project.reactor.axial_cells
        stages = max(int(stages), 1)
        stage_project = Project(
            schema_version=project.schema_version,
            name=project.name,
            reactor=type(project.reactor)(
                kind="CSTR",
                nmax=project.reactor.nmax,
                volume=project.reactor.volume,
                residence_time=project.reactor.residence_time / stages,
                stages=project.reactor.stages,
                axial_cells=project.reactor.axial_cells,
            ),
            kinetics=project.kinetics,
            recipe=project.recipe,
            outputs=project.outputs,
            heat_balance=project.heat_balance,
            substances=list(project.substances),
            polymers=list(project.polymers),
            reaction_steps=list(project.reaction_steps),
            generic_parameters=dict(project.generic_parameters),
            parameters=list(project.parameters),
            reaction_modifier_scripts=dict(project.reaction_modifier_scripts),
        )
        solution_result = None
        stage_initial = project.recipe.initial
        stage_feed = effective_feed_stream(project.recipe)
        for _stage in range(stages):
            stage_recipe = Recipe(
                name=project.recipe.name,
                unit_system=project.recipe.unit_system,
                initial=stage_initial,
                feed=stage_feed,
                feed_tanks=[],
                polymer_feed=list(project.recipe.polymer_feed),
                integration=project.recipe.integration,
                pre_schedule=list(project.recipe.pre_schedule),
                temperature_profile=list(project.recipe.temperature_profile),
                pressure_profile=list(project.recipe.pressure_profile),
                shooting_control=dict(project.recipe.shooting_control),
            )
            stage_project = Project(
                schema_version=stage_project.schema_version,
                name=stage_project.name,
                reactor=stage_project.reactor,
                kinetics=stage_project.kinetics,
                recipe=stage_recipe,
                outputs=stage_project.outputs,
                heat_balance=stage_project.heat_balance,
                substances=list(stage_project.substances),
                polymers=list(stage_project.polymers),
                reaction_steps=list(stage_project.reaction_steps),
                generic_parameters=dict(stage_project.generic_parameters),
                parameters=list(stage_project.parameters),
                reaction_modifier_scripts=dict(stage_project.reaction_modifier_scripts),
            )
            solution_result = self._run_coupled_thermal_cstr(stage_project, t_span, t_eval)
            outlet = SpeciesState.from_array(solution_result.state_history[:3, -1])
            stage_initial = InitialConditions(outlet.monomer, outlet.initiator, outlet.radicals)
            stage_feed = FeedStream(outlet.monomer, outlet.initiator, outlet.radicals, rate=stage_feed.rate)
        if solution_result is None:
            raise ValueError("Thermal cascade requires at least one stage")
        solution_result.metadata["thermal_coupled_stages"] = stages
        solution_result.metadata["reactor_kind_original"] = project.reactor.kind
        return SimulationResult(
            success=solution_result.success,
            message=solution_result.message,
            reactor_kind=project.reactor.kind,
            time=solution_result.time,
            state_history=solution_result.state_history,
            distribution_history=solution_result.distribution_history,
            first_length=solution_result.first_length,
            metadata=solution_result.metadata,
        )

    def _solve_thermal_augmented(
        self,
        project: Project,
        t_span: tuple[float, float],
        t_eval: np.ndarray,
        y0: np.ndarray,
        chemistry_rhs: Callable[[float, np.ndarray, FRPScheme], np.ndarray],
    ):
        kinetics = self._effective_kinetics(project)
        heat = project.heat_balance
        capacity = max(float(heat.heat_capacity) * float(heat.mass_holdup), 1e-12)
        ua = float(heat.heat_transfer) * float(heat.area) if heat.use_heat_exchanger else 0.0
        reference_temperature = float(project.generic_parameters.get("reference_temperature", heat.initial_feed_temp))
        activation_energy = float(project.generic_parameters.get("activation_energy", 0.0))
        gas_constant = float(project.generic_parameters.get("gas_constant", 8.314462618))
        reaction_enthalpy = float(project.generic_parameters.get("reaction_enthalpy", 0.0))
        coolant_default = self._coolant_default(project)

        def thermal_factor(temperature: float) -> float:
            if activation_energy == 0.0:
                return 1.0
            safe_temperature = max(float(temperature), 1e-9)
            safe_reference = max(reference_temperature, 1e-9)
            exponent = activation_energy / gas_constant * (1.0 / safe_reference - 1.0 / safe_temperature)
            return float(np.exp(np.clip(exponent, -50.0, 50.0)))

        def rhs(t: float, state: np.ndarray) -> np.ndarray:
            temperature = float(state[-1])
            factor = thermal_factor(temperature)
            scheme = FRPScheme(
                kp=kinetics.kp * factor,
                kt=kinetics.kt * factor,
                kd=kinetics.kd * factor,
                initiator_efficiency=kinetics.initiator_efficiency,
            )
            chemistry_state = state[:-1]
            chem_rhs = chemistry_rhs(t, chemistry_state, scheme)
            monomer_consumption_rate = max(-float(chem_rhs[0]), 0.0)
            generated_heat_rate = -reaction_enthalpy * monomer_consumption_rate
            coolant = scheduled_coolant_temperature(project.recipe, t, coolant_default)
            additional_heat = scheduled_additional_heat(project.recipe, t, heat.additional_heat)
            exchanger_duty = ua * (temperature - coolant)
            d_temperature = (generated_heat_rate + additional_heat - exchanger_duty) / capacity
            return np.concatenate([chem_rhs, [d_temperature]])

        return solve_ivp(
            rhs,
            t_span,
            y0,
            t_eval=t_eval,
            method=project.recipe.integration.method,
            rtol=project.recipe.integration.rtol,
            atol=project.recipe.integration.atol,
        )

    def _thermal_augmented_result(self, project: Project, solution, *, chemistry_size: int, distribution_slice: slice) -> SimulationResult:
        chemistry_history = solution.y[:chemistry_size, :]
        temperature_history = solution.y[chemistry_size, :]
        distribution_history = chemistry_history[distribution_slice, :]
        heat = project.heat_balance
        ua = float(heat.heat_transfer) * float(heat.area) if heat.use_heat_exchanger else 0.0
        coolant_default = self._coolant_default(project)
        coolant_history = [scheduled_coolant_temperature(project.recipe, float(time), coolant_default) for time in solution.t]
        additional_heat_history = [scheduled_additional_heat(project.recipe, float(time), heat.additional_heat) for time in solution.t]
        heat_duty = [ua * (float(temperature) - float(coolant)) for temperature, coolant in zip(temperature_history, coolant_history)]
        return SimulationResult(
            success=bool(solution.success),
            message=str(solution.message),
            reactor_kind=project.reactor.kind,
            time=solution.t,
            state_history=chemistry_history,
            distribution_history=distribution_history,
            first_length=0,
            metadata={
                "solver_status": getattr(solution, "status", None),
                "backend": "discrete",
                "heat_balance": "coupled_thermal_rhs",
                "thermal_coupled": True,
                "temperature_dependent_kinetics": True,
                "temperature_history": temperature_history.tolist(),
                "heat_duty_history": heat_duty,
                "coolant_temperature_history": coolant_history,
                "additional_heat_history": additional_heat_history,
                "final_temperature": float(temperature_history[-1]),
                "final_heat_duty": float(heat_duty[-1]),
                "final_coolant_temperature": float(coolant_history[-1]),
                "final_additional_heat": float(additional_heat_history[-1]),
            },
        )

    def _coolant_default(self, project: Project) -> float:
        heat = project.heat_balance
        return (
            heat.initial_feed_temp
            if heat.coolant_temperature == 298.15 and heat.initial_feed_temp != 298.15
            else heat.coolant_temperature
        )

    def _run_galerkin_direct_adaptive(self, project: Project, t_span: tuple[float, float], t_eval: np.ndarray) -> SimulationResult:
        integration = project.recipe.integration
        kinetics = self._effective_kinetics(project)
        initial = project.recipe.initial
        mesh = HPMesh.uniform(0.0, float(project.reactor.nmax), cells=integration.galerkin_cells, degree=integration.galerkin_degree)
        field = GalerkinField.project(mesh, lambda x: np.zeros_like(np.asarray(x, dtype=float)))
        species = SpeciesState(initial.monomer, initial.initiator, initial.radicals)
        scheme = FRPScheme(
            kp=kinetics.kp,
            kt=kinetics.kt,
            kd=kinetics.kd,
            initiator_efficiency=kinetics.initiator_efficiency,
        )
        lengths = np.arange(0, project.reactor.nmax + 1, dtype=float)
        species_rows = [species.as_array()]
        distribution_columns = [np.maximum(field.evaluate(lengths), 0.0)]
        dof_history = [mesh.dofs]
        adaptation_events: list[dict[str, object]] = []
        tolerance = float(project.generic_parameters.get("adaptive_tolerance", 1e-3))
        max_cells = int(project.generic_parameters.get("adaptive_max_cells", max(integration.galerkin_cells * 4, integration.galerkin_cells)))
        max_degree = int(project.generic_parameters.get("adaptive_max_degree", max(integration.galerkin_degree + 2, integration.galerkin_degree)))

        current_species = species.as_array()
        current_field = field
        current_mesh = mesh
        for index in range(1, len(t_eval)):
            system = GalerkinFRPBatchSystem(
                mesh=current_mesh,
                initial_field=current_field,
                species=SpeciesState(*map(float, current_species)),
                scheme=scheme,
            )
            solution = system.solve((float(t_eval[index - 1]), float(t_eval[index])), t_eval=np.asarray([float(t_eval[index])]), method=integration.method)
            if not solution.success:
                return self._adaptive_result(
                    project,
                    t_eval[:index],
                    np.asarray(species_rows, dtype=float),
                    np.asarray(distribution_columns, dtype=float).T,
                    False,
                    str(solution.message),
                    dof_history,
                    adaptation_events,
                )
            current_species = solution.y[:3, -1]
            current_field = GalerkinField(current_mesh, solution.y[3:, -1])
            species_rows.append(current_species.copy())
            distribution_columns.append(np.maximum(current_field.evaluate(lengths), 0.0))
            if index < len(t_eval) - 1:
                adapted = adapt_galerkin_field(
                    current_field,
                    tolerance=tolerance,
                    strategy="mixed",
                    max_cells=max_cells,
                    max_degree=max_degree,
                )
                if adapted.changed:
                    current_field = adapted.field
                    current_mesh = adapted.field.mesh
                    adaptation_events.append(
                        {
                            "time": float(t_eval[index]),
                            "dofs": current_mesh.dofs,
                            "h_marked": sorted(adapted.h_marked),
                            "p_marked": sorted(adapted.p_marked),
                            "max_indicator": float(np.max(adapted.indicators)) if adapted.indicators.size else 0.0,
                        }
                    )
            dof_history.append(current_mesh.dofs)

        return self._adaptive_result(
            project,
            t_eval,
            np.asarray(species_rows, dtype=float),
            np.asarray(distribution_columns, dtype=float).T,
            True,
            "adaptive galerkin_direct completed",
            dof_history,
            adaptation_events,
        )

    def _adaptive_result(
        self,
        project: Project,
        time: np.ndarray,
        species_history_rows: np.ndarray,
        distribution_history: np.ndarray,
        success: bool,
        message: str,
        dof_history: list[int],
        adaptation_events: list[dict[str, object]],
    ) -> SimulationResult:
        state_history = np.vstack(
            [
                species_history_rows[:, 0],
                species_history_rows[:, 1],
                species_history_rows[:, 2],
                distribution_history,
            ]
        )
        return SimulationResult(
            success=success,
            message=message,
            reactor_kind=project.reactor.kind,
            time=np.asarray(time, dtype=float),
            state_history=state_history,
            distribution_history=distribution_history,
            first_length=0,
            metadata={
                "solver_status": 0 if success else -1,
                "backend": "galerkin_direct",
                "adaptive_galerkin": True,
                "adaptive_events": adaptation_events,
                "adaptive_event_count": len(adaptation_events),
                "galerkin_dof_history": dof_history,
                "galerkin_dofs": int(dof_history[-1]) if dof_history else 0,
                "galerkin_cells": project.recipe.integration.galerkin_cells,
                "galerkin_degree": project.recipe.integration.galerkin_degree,
                "species_coupled": True,
            },
        )

    def _apply_reaction_step_postprocess(self, project: Project, result: SimulationResult) -> SimulationResult:
        adjusted = result.distribution_history.copy()
        base_params = dict(project.generic_parameters)
        modifier_events: list[dict[str, object]] = []
        if result.time.size > 1:
            dt_values = np.diff(result.time, prepend=result.time[0])
        else:
            dt_values = np.zeros(result.time.size)
        for index, dt in enumerate(dt_values):
            if dt <= 0:
                continue
            rhs = np.zeros_like(adjusted[:, index], dtype=float)
            for step in project.reaction_steps:
                params, event = self._params_for_reaction_step(
                    project,
                    step,
                    base_params,
                    adjusted[:, index],
                    time=float(result.time[index]),
                    index=index,
                )
                if event is not None:
                    modifier_events.append(event)
                rhs += assemble_reaction_step_rhs(adjusted[:, index], step, params)
            adjusted[:, index] = np.maximum(adjusted[:, index] + dt * rhs, 0.0)
        return SimulationResult(
            success=result.success,
            message=result.message,
            reactor_kind=result.reactor_kind,
            time=result.time,
            state_history=result.state_history,
            distribution_history=adjusted,
            first_length=result.first_length,
            metadata={
                **result.metadata,
                "reaction_steps_applied": len(project.reaction_steps),
                "reaction_modifier_events": modifier_events,
            },
        )

    def _params_for_reaction_step(
        self,
        project: Project,
        step,
        base_params: dict[str, float],
        distribution: np.ndarray,
        *,
        time: float,
        index: int,
    ) -> tuple[dict[str, float], dict[str, object] | None]:
        try:
            evaluation = evaluate_modifier_expression(
                step.rate_law.expression,
                scripts=project.reaction_modifier_scripts,
                state=self._reaction_modifier_state(base_params, distribution, time=time),
            )
        except ValueError:
            return base_params, None
        params = dict(base_params)
        value = float(evaluation.values[0])
        params[evaluation.modifier.parameter] = value
        return params, {
            "step": step.name,
            "parameter": evaluation.modifier.parameter,
            "script": evaluation.modifier.script_name,
            "mode": evaluation.modifier.mode,
            "time": time,
            "index": index,
            "value": value,
        }

    @staticmethod
    def _reaction_modifier_state(
        parameters: dict[str, float],
        distribution: np.ndarray,
        *,
        time: float,
    ) -> ScriptCommandState:
        report = from_discrete_distribution(distribution, first_length=0)
        return ScriptCommandState(
            current_concentrations={
                "distribution_total": float(np.sum(distribution)),
                "mass": float(report.mass),
            },
            moments={
                "M0": report.m0,
                "M1": report.m1,
                "M2": report.m2,
                "M3": report.m3,
                "Mn": report.mn,
                "Mw": report.mw,
                "PDI": report.pdi,
                "mass": report.mass,
            },
            parameters=dict(parameters),
            variables={"time": float(time)},
        )

    def _apply_heat_balance(self, project: Project, result: SimulationResult) -> SimulationResult:
        coolant_default = (
            project.heat_balance.initial_feed_temp
            if project.heat_balance.coolant_temperature == 298.15 and project.heat_balance.initial_feed_temp != 298.15
            else project.heat_balance.coolant_temperature
        )
        energy = compute_lumped_energy_balance(
            result.time,
            result.state_history[0, :],
            project.heat_balance,
            reaction_enthalpy=float(project.generic_parameters.get("reaction_enthalpy", 0.0)),
            coolant_temperature_history=np.asarray(
                [
                    scheduled_coolant_temperature(project.recipe, float(time), coolant_default)
                    for time in result.time
                ],
                dtype=float,
            ),
            additional_heat_history=np.asarray(
                [
                    scheduled_additional_heat(project.recipe, float(time), project.heat_balance.additional_heat)
                    for time in result.time
                ],
                dtype=float,
            ),
        )
        coolant_history = [
            scheduled_coolant_temperature(project.recipe, float(time), coolant_default)
            for time in result.time
        ]
        additional_heat_history = [
            scheduled_additional_heat(project.recipe, float(time), project.heat_balance.additional_heat)
            for time in result.time
        ]
        return SimulationResult(
            success=result.success,
            message=result.message,
            reactor_kind=result.reactor_kind,
            time=result.time,
            state_history=result.state_history,
            distribution_history=result.distribution_history,
            first_length=result.first_length,
            metadata={
                **result.metadata,
                "heat_balance": energy.method,
                "temperature_history": energy.temperature.tolist(),
                "heat_duty_history": energy.heat_duty.tolist(),
                "coolant_temperature_history": coolant_history,
                "additional_heat_history": additional_heat_history,
                "final_temperature": float(energy.temperature[-1]),
                "final_heat_duty": float(energy.heat_duty[-1]),
                "final_coolant_temperature": float(coolant_history[-1]) if coolant_history else coolant_default,
                "final_additional_heat": float(additional_heat_history[-1]) if additional_heat_history else project.heat_balance.additional_heat,
            },
        )

    def _apply_recipe_profiles(self, project: Project, result: SimulationResult, t_final: float) -> SimulationResult:
        temp_history = [
            scheduled_temperature(project.recipe, float(time), project.heat_balance.initial_feed_temp)
            for time in result.time
        ]
        pressure_history = [
            scheduled_pressure(project.recipe, float(time), 1.0)
            for time in result.time
        ]
        scheduled_final = apply_pre_schedule(project, t_final)
        metadata = {
            **result.metadata,
            "temperature_setpoint_history": temp_history,
            "pressure_history": pressure_history,
            "final_pressure": float(pressure_history[-1]) if pressure_history else 1.0,
            "scheduled_final_feed_rate": float(effective_feed_stream(scheduled_final.recipe).rate),
            "scheduled_final_residence_time": float(scheduled_final.reactor.residence_time),
            "pre_schedule_steps": len(project.recipe.pre_schedule),
        }
        if "final_temperature" not in metadata:
            metadata["final_temperature"] = float(temp_history[-1]) if temp_history else project.heat_balance.initial_feed_temp
        return SimulationResult(
            success=result.success,
            message=result.message,
            reactor_kind=result.reactor_kind,
            time=result.time,
            state_history=result.state_history,
            distribution_history=result.distribution_history,
            first_length=result.first_length,
            metadata=metadata,
        )

    @staticmethod
    def _effective_kinetics(project: Project):
        params = project.generic_parameters
        base = project.kinetics
        return type(base)(
            kp=float(params.get("GP_kp", base.kp)),
            kt=float(params.get("GP_kt", base.kt)),
            kd=float(params.get("GP_kd", base.kd)),
            initiator_efficiency=float(params.get("GP_f", base.initiator_efficiency)),
        )

    @staticmethod
    def _result_from_solution(success: bool, message: str, reactor_kind: str, solution) -> SimulationResult:
        if reactor_kind == "Semi-batch":
            distribution = solution.y[3:-1, :]
        else:
            distribution = solution.y[3:, :]
        return SimulationResult(
            success=success,
            message=message,
            reactor_kind=reactor_kind,
            time=solution.t,
            state_history=solution.y,
            distribution_history=distribution,
            metadata={"solver_status": getattr(solution, "status", None)},
        )

    def _output_points_for_target(self, target: float) -> int:
        integration = self.project.recipe.integration
        if target <= 0.0:
            return 2
        full_time = max(float(integration.t_final), 1e-12)
        fraction = min(float(target) / full_time, 1.0)
        return max(2, int(round(max(int(integration.output_points), 2) * fraction)))

    def _default_step_size(self) -> float:
        integration = self.project.recipe.integration
        intervals = max(int(integration.output_points) - 1, 1)
        return float(integration.t_final) / intervals

    @staticmethod
    def _with_actual_values_metadata(result: SimulationResult) -> SimulationResult:
        actual_values = result.actual_values_history()
        metadata = {
            **result.metadata,
            "actual_values": actual_values,
            "step_index": int(len(actual_values) - 1),
            "stepsize": float(actual_values[-1]["stepsize"]) if actual_values else 0.0,
            "n_variables": int(result.state_history.shape[0]),
        }
        return SimulationResult(
            success=result.success,
            message=result.message,
            reactor_kind=result.reactor_kind,
            time=result.time,
            state_history=result.state_history,
            distribution_history=result.distribution_history,
            first_length=result.first_length,
            metadata=metadata,
        )

    @staticmethod
    def _with_simulation_mode_metadata(
        result: SimulationResult,
        project: Project,
        request: SimulationRequest,
    ) -> SimulationResult:
        integration = project.recipe.integration
        mode = request.mode or integration.simulation_mode
        metadata = {
            **result.metadata,
            "simulation_mode": mode,
            "include_monte_carlo": bool(integration.include_monte_carlo),
            "use_tau_leaping": bool(integration.use_tau_leaping),
        }
        state_history = result.state_history
        if mode == "moments":
            moments = result.moment_history()
            names = ("M0", "M1", "M2", "Mn", "Mw", "PDI")
            state_history = np.vstack([moments[name] for name in names])
            metadata = {
                **metadata,
                "moments_backend": "projected_distribution_moments",
                "moment_state_names": names,
                "n_variables": int(state_history.shape[0]),
            }
            projected = SimulationResult(
                success=result.success,
                message=result.message,
                reactor_kind=result.reactor_kind,
                time=result.time,
                state_history=state_history,
                distribution_history=result.distribution_history,
                first_length=result.first_length,
                metadata=metadata,
            )
            metadata = {**metadata, "actual_values": projected.actual_values_history()}
        return SimulationResult(
            success=result.success,
            message=result.message,
            reactor_kind=result.reactor_kind,
            time=result.time,
            state_history=state_history,
            distribution_history=result.distribution_history,
            first_length=result.first_length,
            metadata=metadata,
        )

    @staticmethod
    def _with_run_control_metadata(result: SimulationResult, *, target_time: float, requested_step: bool) -> SimulationResult:
        metadata = {
            **result.metadata,
            "run_control": {
                "target_time": float(target_time),
                "requested_step": bool(requested_step),
                "step_index": int(result.metadata.get("step_index", max(len(result.time) - 1, 0))),
                "stepsize": float(result.metadata.get("stepsize", 0.0)),
                "n_variables": int(result.metadata.get("n_variables", result.state_history.shape[0])),
            },
        }
        return SimulationResult(
            success=result.success,
            message=result.message,
            reactor_kind=result.reactor_kind,
            time=result.time,
            state_history=result.state_history,
            distribution_history=result.distribution_history,
            first_length=result.first_length,
            metadata=metadata,
        )

    @staticmethod
    def _emit_steps(callbacks: SimulationCallbacks, result: SimulationResult) -> None:
        if callbacks.on_step is None:
            return
        moments = result.moment_history()
        count = len(result.time)
        for i, t in enumerate(result.time):
            if callbacks.should_stop and callbacks.should_stop():
                break
            callbacks.on_step(
                {
                    "time": float(t),
                    "progress": float((i + 1) / count),
                    "Mn": float(moments["Mn"][i]),
                    "Mw": float(moments["Mw"][i]),
                    "PDI": float(moments["PDI"][i]),
                }
            )
            if callbacks.on_progress:
                callbacks.on_progress(float((i + 1) / count))

    @staticmethod
    def _emit_general_steps(callbacks: SimulationCallbacks, result: SimulationResult) -> None:
        count = len(result.time)
        species_names = list(result.metadata.get("species_names", []))
        for i, t in enumerate(result.time):
            if callbacks.should_stop and callbacks.should_stop():
                break
            if callbacks.on_step is not None:
                callbacks.on_step(
                    {
                        "time": float(t),
                        "progress": float((i + 1) / count),
                        **{
                            f"conc:{name}": float(result.state_history[index, i])
                            for index, name in enumerate(species_names)
                        },
                    }
                )
            if callbacks.on_progress:
                callbacks.on_progress(float((i + 1) / count))

    @staticmethod
    def _log(callbacks: SimulationCallbacks, message: str) -> None:
        if callbacks.on_log:
            callbacks.on_log(message)
