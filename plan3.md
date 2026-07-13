# PREDICI Clone 개발 계획 v3.1

이 문서는 `plan.md`의 discrete Galerkin h-p 기반 PBE/중합 반응기 계획과 `plan2.md`의 PySide6 GUI 계획을 통합하고, 다음 두 문서에서 확인한 실제 PREDICI 기능을 반영해 다시 정리한 실행 계획이다.

- `Predici11_Overview.pdf`: PREDICI 11 기능 개요, UI 흐름, 모델링/recipe/output/parameter estimation/interoperability
- `Predici_Maxwell.pdf`: 2024/25 Maxwell 신규 기능, dashboard, generic outputs, multi-steps, heat balance, shooting control, OLE command 확장

목표는 PREDICI 자체를 복제하는 것이 아니라, 같은 문제 영역을 다루는 독립 구현체를 단계적으로 만드는 것이다. 즉, “PBE/Galerkin solver + polymer reaction DSL + reactor recipes + professional PySide6 interface + validation/fitting workflow”를 갖춘 연구 및 엔지니어링용 애플리케이션을 만든다.

---

## 0. 제품 목표

### 0.1 핵심 사용자

- polymer kinetics 연구자
- 반응기/공정 엔지니어
- MWD/GPC/SEC 데이터를 fitting해야 하는 모델러
- batch, semi-batch, CSTR, PFR, cascade 조건을 비교해야 하는 사용자
- 논문 benchmark와 내부 실험 데이터를 재현 가능한 방식으로 관리해야 하는 사용자

### 0.2 핵심 가치

1. 중합 반응을 chain-length distribution 관점에서 모델링한다.
2. discrete chain backend와 Galerkin h-p backend를 모두 지원한다.
3. reactor recipe, feed, temperature/pressure profile, output, fitting 설정을 하나의 project로 관리한다.
4. GUI는 전문 공학 소프트웨어처럼 조밀하고 안정적인 작업 환경을 제공한다.
5. 모든 GUI 기능은 CLI/API에서도 재사용 가능해야 한다.

### 0.3 비목표

- PREDICI 파일 포맷 또는 내부 알고리즘의 역공학
- PREDICI UI의 픽셀 단위 복제
- 검증되지 않은 그림 digitization 데이터의 무분별한 포함
- 초기 단계에서 모든 polymerization family 완전 지원

---

## 1. 현재 저장소 기준선

현재 구현된 기능:

- `core`
  - Legendre basis
  - h-p mesh
  - Galerkin projection/evaluation
  - moments
  - modal-tail error indicator
- `kinetics`
  - 최소 FRP scheme
  - propagation shift
  - termination loss
- `integrator`
  - SciPy BDF/Radau 계열 사용 가능 구조
  - finite-difference sparse Jacobian helper
- `reactor`
  - Batch
  - Semi-batch
  - CSTR
- `postprocess`
  - MWD plot
  - moment report
  - CSV/XLSX export
  - Flory probability fitting
  - mixture Schulz-Flory distribution
- `validation`
  - Flory-Schulz analytic benchmark
  - Fogler fractionation example
  - multi-site Schulz-Flory synthetic benchmark
- `app`
  - PySide6 prototype GUI
  - reactor selection
  - parameter input
  - simulation run
  - benchmark loading
  - distribution plot
  - moment table
  - CSV export
- `tests`
  - core, reactor, postprocess, validation, GUI smoke tests

현재 한계:

- GUI가 아직 전문 툴 수준의 dock/tab/model-builder 구조가 아니다.
- GUI에서 simulation을 직접 호출한다. worker thread와 engine boundary가 필요하다.
- project schema, recipe schema, result manifest가 없다.
- reaction DSL은 FRP 최소 구현에 가깝다.
- Galerkin core가 reactor/kinetics RHS와 완전히 연결되지 않았다.
- fitting은 Flory probability 수준이며 multi-experiment PE workflow가 아니다.
- script interpreter, generic outputs, dashboard, shooting control, heat exchanger 같은 PREDICI식 고급 기능은 아직 계획 단계다.

---

## 2. PDF 기반 기능 요구사항

### 2.1 Predici11_Overview.pdf에서 반영할 항목

문서에서 확인한 핵심 기능:

- macromolecular system의 kinetic, process, property modeling
- radical copolymerization, polycondensation, living polymerization, emulsion/suspension, Ziegler-Natta 계열 적용 가능성
- open and modular modeling framework
- polymer properties: MWD, composition, branching
- scalar outputs: concentration, conversion, product indices, arbitrary outputs
- stochastic results and detailed chain analysis
- controls: production strategies, safety requirements
- parameters: local/global results, sensitivity analysis, sampling
- recipes: CSTR batch/feed/continuous, PFR, cascades
- scripting: ODE/DAE, rates, outputs, equations
- experimental data and parameter estimation
- open interfaces: Cape-Open, OLE, Matlab
- user workflow:
  - chemical model build
  - recipe and initial condition input
  - immediate result visualization
  - detailed chain structure exploration
- model customization:
  - reactor setup
  - substances
  - polymers
  - reaction parameters
  - reaction steps
- recipe capabilities:
  - polymer species, particles, profile data such as GPC/PSD input
  - temperature and pressure control
  - conversion of input types
  - open number of feed tanks
- dynamic outputs:
  - configurable chart administration
  - multiple graphics in one chart
  - comparison to reference results
  - live changes while simulations are running
  - export selected/all data
- extended features:
  - hybrid Monte Carlo solver
  - sensitivity analysis
  - recipe variation
  - PDE solver for spatial profiles
  - particle size distribution integration
- parameter estimation:
  - any number/type of parameters
  - any number/type of experiments
  - any model/data type comparison
  - global search
  - local search with correlation analysis
  - uncertainty and sampling
  - sensitivity, sigma-point, grid variation
  - simulated annealing
  - Gauss-Newton/local search
  - condition/correlation diagnostics
  - mapping experimental data to model outputs
- optimization and optimal control:
  - scalar objectives
  - full GPC/MWD objectives
  - batch time
  - temperature profiles
  - feed profiles
  - startup
  - model parameters

### 2.2 Predici_Maxwell.pdf에서 반영할 항목

문서에서 확인한 Maxwell 신규/확장 기능:

- vectors, matrices, tensors, global variables
- script extensions:
  - loops
  - object-style commands
  - shortcuts
  - array access
- smaller and better organized component windows
- new Multi-Steps:
  - common steps reused across different sites/reactors
  - GUI support
  - generic parameters `GP_xxx`
- extended heat balance:
  - heat exchanger
  - more options
- shooting control:
  - integrated iteration and parameter tuning
  - standard setups accessible by automation interface
- recipes:
  - integration control settings
  - tube reactors
  - unit system per recipe
  - feed of polymer in recipes
  - shooting control
  - pre-schedule
- output extensions:
  - new Generic Outputs
  - user-defined configuration
  - groups: reactor, heat balance, species
  - moments of GPC outputs
  - convolution for GPC output variables
  - time-axis shift by script
  - extended online data
- model extensions:
  - PolymerPartition
  - PDEs/PSDs: FeedProfile, FlowDist, FlowSolve, FluidBalance
  - script commands for sums/holdups/distribution holdups
  - lumping in reactor
- script editor:
  - direct definition of output
  - project variables directly accessible
- dashboard:
  - model and live information in one window
- project settings:
  - simulation time
  - project lists with more information
  - quick access buttons
- active-module overview:
  - important for multi-site models
  - shows all active reactions
- parameter estimation:
  - MDF data trimming
  - synopsis tab
  - batches tab
  - reference temperature treatment
- automation/API examples:
  - create recipe
  - set enthalpy
  - get distribution points
  - get distribution moments including M0-M3, Mn, Mw, Mz, PDI, AMW, mass
  - activate detailed iteration
  - activate quick iteration
  - configure heat exchanger
  - check enthalpy

---

## 3. 전체 아키텍처

### 3.1 원칙

Core 계산 로직은 Qt를 모른다. GUI는 engine API만 호출한다.

```text
predici_clone/
  core/                 # Galerkin, mesh, basis, moments, error estimator
  kinetics/             # reaction DSL, rate laws, RHS assembly
  integrator/           # solvers, Jacobian, adaptive loop
  reactor/              # batch, semibatch, cstr, pfr, cascade, energy
  postprocess/          # plots, reports, fitting helpers, exports
  validation/           # benchmark cases and benchmark runner
  api/                  # project schema, project IO, public automation API
  engine/               # simulation/fitting execution boundary
  app/                  # PySide6 GUI only
    models/
    views/
    workers/
    dialogs/
    resources/
  tests/
  examples/
```

### 3.2 Engine boundary

`engine/simulation_engine.py`는 GUI, CLI, tests가 모두 사용하는 유일한 실행 경계다.

```python
class SimulationEngine:
    def __init__(self, project: Project):
        self.project = project

    def run(self, request: SimulationRequest, callbacks: SimulationCallbacks | None = None) -> SimulationResult:
        ...
```

`callbacks`:

- `on_log(message)`
- `on_progress(fraction)`
- `on_step(snapshot)`
- `on_grid_adapt(info)`
- `should_stop() -> bool`

### 3.3 Result object

`SimulationResult`는 다음을 포함한다.

- solver status
- time grid
- species history
- distribution history
- final distribution
- moments history
- output channels
- reactor metadata
- recipe metadata
- benchmark/fitting metadata
- warnings

---

## 4. Project Schema

### 4.1 파일 목표

PREDICI식 all-in-one project administration을 구현하기 위해 project, model, recipe, outputs, results를 한 스키마로 관리한다.

초기 포맷:

- `project.predici.json`
- 결과 대용량 배열은 `results/run_xxx/*.npz`

### 4.2 스키마 구성

`api/project_schema.py`

- `Project`
  - schema_version
  - name
  - units
  - substances
  - polymers
  - reaction_groups
  - reactor_configs
  - recipes
  - output_configs
  - fitting_configs
  - result_manifest

- `Substance`
  - name
  - kind
  - molecular_weight
  - density
  - heat_capacity
  - user_properties

- `Polymer`
  - name
  - monomer_units
  - distribution_kind
  - measured_profiles

- `ReactionStep`
  - name
  - type
  - reactants
  - products
  - rate_law
  - enthalpy
  - enabled
  - site
  - reactor_scope
  - generic_parameters

- `Recipe`
  - name
  - unit_system
  - simulation_time
  - integration_control
  - initial_conditions
  - feed_tanks
  - pre_schedule
  - temperature_profile
  - pressure_profile
  - shooting_control

- `OutputConfig`
  - scalar outputs
  - distribution outputs
  - generic outputs
  - chart layouts
  - time shift
  - convolution settings

- `FittingConfig`
  - experiments
  - parameter bounds
  - objectives
  - optimizer settings
  - trimming
  - reference temperature

### 4.3 Generic parameters

Maxwell의 `GP_xxx` 개념을 반영한다.

목표:

- multi-site 또는 multi-reactor 모델에서 공통 reaction step template을 재사용한다.
- site/reactor별 parameter binding만 바꾼다.

예:

```json
{
  "name": "propagation_template",
  "type": "Propagation",
  "rate_law": "GP_kp * M * R",
  "generic_parameters": ["GP_kp"]
}
```

---

## 5. Reaction DSL과 Multi-Step

### 5.1 기본 reaction modules

초기 지원:

- Initiation
- Propagation
- TerminationDisproportionation
- TerminationCombination
- ChainTransferToMonomer
- ChainTransferToAgent
- Branching placeholder
- Scission
- PolymerPartition placeholder

확장 후보:

- RAFT
- NMP
- ATRP
- condensation/polyurethane/polyester
- catalytic multi-site polymerization
- emulsion/suspension placeholders

### 5.2 Multi-Step

Maxwell의 “common steps reused for different sites/reactors”를 반영한다.

구조:

- `StepTemplate`
- `StepInstance`
- `ParameterBinding`
- `SiteDefinition`
- `ReactorScope`

검증:

- 같은 propagation template이 site A/B에서 서로 다른 `GP_kp`로 작동한다.
- active-module overview에서 활성 reaction 목록이 정확히 표시된다.

---

## 6. Numerical Core Roadmap

### 6.1 Backends

두 backend를 병행한다.

- `DiscreteBackend`
  - chain length vector 직접 적분
  - 빠른 검증과 GUI prototype에 적합

- `GalerkinBackend`
  - h-p mesh coefficient 적분
  - PREDICI식 핵심 solver 목표

### 6.2 Galerkin 결합

필수 구성:

- `GalerkinState`
- `OperatorAssembler`
- propagation operator
- termination/loss operator
- source projection
- convolution operator
- h/p adapt loop
- discrete-continuous boundary handling

### 6.3 Integration control

Recipe별 integration control을 지원한다.

- solver method: BDF, Radau
- rtol/atol
- max step
- initial step
- event handling
- adaptive mesh option
- step failure policy

### 6.4 Verification

- Flory-Schulz analytic moments
- moment conservation across h refinement
- p refinement smoothness check
- discrete/Galerkin backend comparison
- stiff solver regression

---

## 7. Reactor and Process Models

### 7.1 기존 구현 유지

- Batch
- Semi-batch
- CSTR

### 7.2 추가 대상

- PFR / tube reactor
- CSTR cascade
- recipe-level feed tanks
- polymer feed in recipe
- pre-schedule
- temperature/pressure control
- reactor startup profile

### 7.3 Heat Balance

Maxwell의 extended heat balance와 heat exchanger를 반영한다.

`reactor/energy_balance.py`

- isothermal mode
- adiabatic mode
- jacket/heat exchanger mode
- reaction enthalpy
- heat transfer coefficient
- heat exchange area
- coolant/feed temperature
- counter-current flag placeholder

### 7.4 Shooting Control

목표:

- 목표 outlet temperature
- target conversion
- target Mn/Mw/PDI
- target MWD objective

조정 대상:

- feed rate
- reactor temperature
- coolant mass flow
- additional heat
- residence time

구현:

- `engine/shooting.py`
- 내부적으로 `scipy.optimize.root` 또는 `least_squares`
- GUI에서는 recipe의 “Shooting” tab에서 설정

---

## 8. Outputs, Dashboard, Reports

### 8.1 Generic Outputs

Maxwell의 Generic Outputs 개념을 반영한다.

Output groups:

- reactor
- heat balance
- species
- polymer distribution
- GPC/MWD
- user script
- fitting residual

각 output은 다음을 가진다.

- name
- expression or provider
- unit
- group
- enabled
- chart target
- export policy
- time shift
- convolution setting

### 8.2 Distribution Moments

Automation API와 report 모두 다음 moments를 제공한다.

- M0
- M1
- M2
- M3
- Mn
- Mw
- Mz
- PDI
- AMW
- mass

현재 `MomentReport`는 M0-M2/Mn/Mw/PDI만 있으므로 확장한다.

### 8.3 GPC/SEC Output

지원 목표:

- chain length to molecular weight transform
- number distribution
- weight distribution
- log molecular weight axis
- convolution/broadening option
- measured GPC overlay
- moments of GPC outputs

### 8.4 Dashboard

Maxwell의 “model and live information in one window”를 반영한다.

Dashboard 구성:

- run status
- current recipe
- active reactor
- active modules
- key scalar outputs
- Mn/Mw/PDI cards
- conversion
- temperature/pressure
- live MWD preview
- warnings
- solver diagnostics

Professional UI 기준:

- dashboard는 장식적 hero 화면이 아니라 고밀도 engineering overview여야 한다.
- 숫자는 table/card 혼합으로 정렬하고 단위를 명확히 표시한다.
- chart는 축, 단위, legend, export affordance를 갖춘다.
- 상태 색은 절제된 palette를 사용한다.

---

## 9. Professional PySide6 GUI 계획

### 9.1 디자인 목표

GUI는 “데모 폼”이 아니라 전문 데스크톱 엔지니어링 툴이어야 한다.

품질 기준:

- QMainWindow + dock + tab 기반 생산성 중심 layout
- 좌측 project tree, 중앙 workspace, 우측 inspector, 하단 log/progress
- toolbar와 menu bar 제공
- undo/redo 가능한 편집 workflow
- dense but readable table UI
- 긴 계산 중 UI freeze 없음
- 결과 plot은 live update 가능
- 모든 control에 명확한 label, unit, validation state
- 입력 오류는 inline warning과 log로 표시
- project save/load/recent files 지원
- light/dark neutral theme 중 최소 하나의 완성도 있는 stylesheet 제공

색/시각 기준:

- 과도한 gradient, hero section, marketing layout 금지
- 공학 도구에 맞는 restrained palette
- 8px 이하 radius의 compact panel/card
- table, split pane, dock, toolbar 중심
- chart colors는 비교 가능한 6-8개 palette로 제한
- font size는 viewport width로 scaling하지 않는다
- text overflow가 없는지 offscreen screenshot 또는 smoke test로 확인한다.

### 9.2 Main Window

```text
MenuBar:
  File Edit View Model Recipe Simulate Analysis Fitting Tools Help

ToolBar:
  New Open Save | Undo Redo | Run Stop | Export | Layout

Left Dock:
  Project Tree
    Project
    Units
    Substances
    Polymers
    Reaction Groups
    Reactors
    Recipes
    Outputs
    Experiments
    Results

Center Tabs:
  Dashboard
  Model Builder
  Recipe Editor
  Simulation
  MWD Viewer
  Fitting
  Script

Right Dock:
  Inspector
    selected item properties
    validation messages

Bottom Dock:
  Log
  Progress
  Solver Diagnostics
```

### 9.3 Model Builder

기능:

- reactor setup
- substance table
- polymer definition
- reaction group table
- reaction step editor
- multi-step templates
- generic parameter binding
- active-module overview
- enabled/disabled reaction toggles

UI:

- 좌측 reaction module palette
- 중앙 reaction table
- 우측 inspector
- 하단 validation panel

### 9.4 Recipe Editor

기능:

- initial concentrations
- feed tanks
- polymer feed
- unit system per recipe
- integration control
- pre-schedule
- temperature/pressure profile
- tube reactor settings
- shooting control settings

UI:

- recipe list
- tabs: Initial, Feeds, Profiles, Integration, Shooting
- table editing with unit columns
- copy recipe / compare recipes

### 9.5 Simulation Panel

기능:

- backend: discrete/galerkin
- solver method
- tolerance
- mesh settings
- run/stop/pause
- progress
- solver diagnostics
- live scalar output table

### 9.6 MWD Viewer

기능:

- mole/weight distribution toggle
- chain length / molecular weight / log axis
- GPC convolution toggle
- time slider
- overlay multiple runs
- overlay benchmark/reference
- export CSV/PNG/PDF
- moments table

### 9.7 Fitting Panel

Predici11의 PE workflow를 반영한다.

Tabs:

- Experiments
- Data Mapping
- Parameters
- Sensitivity
- Global Search
- Local Search
- Uncertainty
- Results

기능:

- MDF/CSV data import
- data trimming
- column to output mapping
- multiple experiments
- parameter bounds/fixed flags
- sensitivity: Monte Carlo, sigma-point, grid
- global search: differential evolution, dual annealing
- local search: least squares/Gauss-Newton style
- correlation/condition diagnostics
- uncertainty summary
- residual plot
- goodness-of-fit live update

### 9.8 Script Panel

Maxwell script extensions를 반영하되 안전하게 단계 도입한다.

Phase 1:

- user-defined output expression
- project variables read access
- selected helper functions

Phase 2:

- loops
- array access
- object-style commands
- shortcuts
- direct output definition

주의:

- 임의 `exec`는 기본 비활성화
- script namespace 제한
- project mutation은 command API를 통해서만 허용

---

## 10. GUI Worker Thread

장시간 simulation/fitting은 반드시 worker에서 수행한다.

```python
class SimulationWorker(QObject):
    progress = Signal(float)
    step_done = Signal(object)
    finished = Signal(object)
    error = Signal(str)
    log = Signal(str)

    @Slot()
    def run(self): ...

    @Slot()
    def request_stop(self): ...
```

규칙:

- GUI thread는 core object를 직접 변경하지 않는다.
- worker에는 project snapshot을 넘긴다.
- signal payload는 immutable dataclass 또는 copy된 dict/array summary를 사용한다.
- plot update는 50-100ms batch update로 제한한다.
- worker 강제 종료 금지. solver loop에서 stop flag 확인.

테스트:

- offscreen GUI smoke
- worker start/finish
- stop request
- error propagation
- progress signal ordering

---

## 11. Parameter Estimation and Optimization

### 11.1 PE Workflow

Predici11 PE 순서를 반영한다.

1. parameter guess 또는 literature estimate 입력
2. sensitivity analysis로 dependency 확인
3. global search로 initial guess 개선
4. local search로 optimum 계산
5. uncertainty/correlation/condition 평가
6. data 추가 또는 model 개선
7. PE configuration 저장

### 11.2 Experiments

하나의 fitting config는 여러 experiment를 가진다.

- experiment name
- data file
- measured columns
- mapped model outputs
- trimming window
- weights
- units
- notes

### 11.3 Objectives

- scalar outputs: conversion, concentration, temperature, MFI placeholder
- moments: Mn, Mw, Mz, PDI
- full MWD/GPC data
- combined weighted objective
- multiple experiments combined residual

### 11.4 Optimizers

- local: `scipy.optimize.least_squares`
- global: `differential_evolution`, `dual_annealing`
- shooting: `root`, `least_squares`
- sensitivity:
  - finite difference
  - Monte Carlo
  - sigma-point: `2*p + 1` evaluations
  - grid for up to 3 parameters

### 11.5 Diagnostics

- residual
- parameter covariance approximation
- correlation matrix
- condition number
- confidence interval approximation
- essential direction placeholder

---

## 12. Automation API and Interoperability

PREDICI의 OLE/COM 성격을 Python public API로 제공한다.

`api/automation.py`

초기 API:

- `create_recipe(project, recipe_name, option)`
- `set_enthalpy(project, step_type, reactant, value)`
- `get_dist_points(result, names, normed_output, graphic_weight, log_axis, x_as_mol_weight)`
- `get_dist_moments(result, distribution_name)`
- `set_dist_lumping(project, on_off)`
- `get_reactor_pressure(result, reactor_name)`
- `activate_detailed_iteration(project, reactor_name, spec_type, tune_type, spec_value)`
- `set_heat_exchanger(project, reactor_name, ...)`
- `check_enthalpy(project, reactor_name)`

Export:

- Excel
- text/CSV
- JSON project
- NPZ result arrays
- optional Matlab/C moment-equation export later

Cape-Open은 장기 목표로만 둔다.

---

## 13. Validation and Benchmark Plan

### 13.1 원칙

- source, note, derivation을 모든 benchmark에 기록한다.
- 공개 식 또는 표 기반 데이터만 기본 포함한다.
- synthetic benchmark는 synthetic임을 명시한다.
- figure digitization은 license/metadata가 확인된 경우에만 별도 폴더에 둔다.

### 13.2 Benchmark 목록

Fast benchmarks:

- Flory-Schulz analytic distribution
- Fogler fractionation table
- multi-site Schulz-Flory mixture
- discrete vs Galerkin moment comparison
- CSTR steady-state trend
- semi-batch feed mass trend

Medium benchmarks:

- synthetic FRP parameter recovery
- recipe variation comparison
- cascade convergence to PFR approximation
- GPC convolution moment check

Slow benchmarks:

- global search recovery
- sensitivity Monte Carlo
- sigma-point sensitivity
- fitting with multiple experiments

### 13.3 Benchmark Runner

`validation/benchmark_runner.py`

출력:

- PASS/FAIL
- expected/actual
- tolerance
- source
- runtime
- warnings

---

## 14. Packaging and Distribution

### 14.1 Packaging target

초기 target:

- Windows PyInstaller build

후보:

- PyInstaller: 기본
- Nuitka: 성능/배포 안정화 후 검토

### 14.2 Build 산출물

```text
dist/
  PrediciClone/
    PrediciClone.exe
    examples/
    benchmarks/
```

### 14.3 Packaging 검증

- clean venv에서 build
- exe 실행
- sample project open
- simulation run
- benchmark load
- CSV/PNG export

---

## 15. Milestone Roadmap

| 단계 | 목표 | 산출물 | 검증 |
|---|---|---|---|
| M8 | Project schema + SimulationEngine | `api/project_schema.py`, `engine/simulation_engine.py` | 기존 examples/GUI가 engine 경유 |
| M9 | Professional GUI shell | dock/tabs/menu/toolbar/project tree/inspector/log | offscreen smoke + manual review |
| M10 | Worker thread | `SimulationWorker`, cancellation, progress/log signal | long run 중 GUI freeze 없음 |
| M11 | Project save/load | `.predici.json`, result manifest | 저장/로드 후 동일 simulation |
| M12 | Output system | Generic outputs, dashboard, M3/Mz/AMW/mass moments | output tests |
| M13 | Reaction DSL v1 + Multi-Step | templates, generic parameters, active module overview | FRP equivalence |
| M14 | Recipe editor v1 | feeds, unit system, integration control, pre-schedule | recipe tests |
| M15 | Galerkin backend coupling | operator assembler, backend selection | discrete/Galerkin benchmark |
| M16 | Reactor expansion | PFR, cascade, heat balance placeholder | cascade/PFR tests |
| M17 | Fitting workflow v1 | experiments, mapping, least_squares, residual plot | synthetic recovery |
| M18 | Sensitivity/global search | sigma-point, MC, dual annealing | PE benchmark |
| M19 | Shooting control | target/tune setup, heat exchanger hooks | shooting test |
| M20 | Scripting v1 | user outputs, safe expression namespace | scripted output test |
| M21 | Packaging | PyInstaller config | exe smoke |

---

## 16. 우선 구현 순서

가장 먼저 해야 할 것은 professional GUI를 바로 크게 만드는 것이 아니라, GUI가 의존할 안정된 project/engine boundary를 만드는 것이다.

1. `Project` schema
2. `SimulationEngine`
3. GUI shell redesign
4. worker thread
5. project save/load
6. output/dashboard system
7. recipe editor
8. reaction DSL/multi-step
9. fitting workflow

단, 사용자가 체감하는 GUI 품질을 빠르게 끌어올리기 위해 M9는 M8 직후 진행한다.

---

## 17. Professional GUI Acceptance Criteria

M9 완료 조건:

- 창 제목, 메뉴, toolbar, status bar가 있다.
- 좌측 project tree가 있다.
- 중앙 workspace가 최소 Dashboard, Simulation, MWD Viewer tab을 가진다.
- 우측 inspector가 선택 항목의 속성을 표시한다.
- 하단 log/progress dock이 있다.
- Run/Stop 버튼이 분리되어 있다.
- default window size에서 text overlap이 없다.
- offscreen smoke test가 통과한다.
- manual run에서 batch/semi-batch/CSTR simulation을 실행하고 plot/moment가 갱신된다.
- benchmark를 load하고 overlay 또는 단독 view로 볼 수 있다.
- CSV export가 가능하다.
- stylesheet가 적용되어 기본 Qt widget 모음처럼 보이지 않는다.

Professional polish checklist:

- compact spacing
- consistent labels and units
- table headers readable
- numeric columns right-aligned
- validation errors inline
- muted engineering color palette
- no decorative hero/marketing layout
- chart grid/legend/axis labels present
- recent files and sample project quick action

---

## 18. 리스크

### 18.1 Galerkin backend 복잡도

대응:

- discrete backend를 검증 기준으로 유지
- backend adapter interface 도입
- moments 먼저 검증, full MWD는 이후 비교

### 18.2 GUI 과확장

대응:

- M9는 shell과 현재 기능의 전문화에 집중
- model builder/fitting/script는 단계적으로 탭만 추가 후 기능 확장

### 18.3 Worker thread race condition

대응:

- project snapshot 실행
- GUI에는 result snapshot만 전달
- core object 직접 공유 금지

### 18.4 Benchmark 신뢰도

대응:

- 모든 benchmark에 source/note/expected 기록
- synthetic과 literature-derived를 명확히 분리

### 18.5 Packaging

대응:

- PyInstaller는 마지막 단계
- 먼저 source 실행 안정화
- SciPy/PySide6/matplotlib DLL 포함 테스트

---

## 19. 다음 작업 M8/M9 구체 계획

### M8: Project schema + SimulationEngine

작업:

1. `predici_clone/api/project_schema.py`
2. `predici_clone/api/project_io.py`
3. `predici_clone/engine/simulation_result.py`
4. `predici_clone/engine/simulation_engine.py`
5. 기존 example과 GUI가 engine API를 사용하도록 변경
6. tests 추가

검증:

```powershell
python -m pytest -q
python examples\industrial_semibatch_cstr.py
```

### M9: Professional GUI Shell

작업:

1. `MainWindow`를 QMainWindow dock/tab 구조로 재작성
2. Project Tree dock
3. Inspector dock
4. Dashboard tab
5. Simulation tab
6. MWD Viewer tab
7. Log/Progress dock
8. Toolbar/Menu/Status bar
9. 기본 stylesheet
10. offscreen smoke test 갱신

검증:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -c "from PySide6.QtWidgets import QApplication; from predici_clone.app.main_window import MainWindow; app=QApplication([]); w=MainWindow(); print(w.windowTitle(), w.size().width(), w.size().height())"
python -m pytest -q
```

---

## 20. 문서 출처 반영 메모

이 계획에 반영된 주요 PDF 항목:

- `Predici11_Overview.pdf`
  - page 3: 적용 polymerization families
  - page 4: open modular framework, outputs, controls, PE, interoperability
  - page 5: UI workflow
  - page 10: basic features, all-in-one project administration, dynamic output, recipes, scripts
  - page 14-18: model customization, recipes, scripts, dynamic outputs
  - page 20: Monte Carlo, sensitivity, recipe variation, PDE/PSD
  - page 25: Excel/text, Cape-Open, OLE/COM, Matlab/C export, user database
  - page 27-43: parameter estimation, sensitivity, global search, local search, optimization/control

- `Predici_Maxwell.pdf`
  - page 2: vectors/matrices/tensors/global variables, script extensions, multi-steps, generic parameters, heat balance, shooting control, OLE/COM commands
  - page 3: recipe integration control, tube reactors, unit system, polymer feed, pre-schedule
  - page 4: generic outputs, output groups, GPC moments, convolution, time-axis shift, online data
  - page 5: PolymerPartition, PDE/PSD extensions, holdup/sum commands, reactor lumping
  - page 6: script editor direct output and project variables
  - page 7: dashboard
  - page 9-10: project settings, quick access, active-module overview
  - page 11-13: PE additions and automation/API command examples
