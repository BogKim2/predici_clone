GUI 사용법
==========

전체 레이아웃
-------------

GUI는 ``QMainWindow`` 기반의 전문 공정 시뮬레이션 작업 환경으로 구성되어 있다.

* 상단: menu bar, toolbar, run/stop/export action
* 왼쪽 dock: project tree
* 중앙 workspace: Dashboard, Model Builder, Recipe Editor, Simulation, MWD Viewer, Fitting, Script tab
* 오른쪽 dock: inspector와 validation message
* 하단 dock/status bar: log, progress, solver status

Dashboard
---------

``Dashboard`` 는 현재 프로젝트와 최근 시뮬레이션 결과를 요약한다.

* reactor kind
* backend
* key generic outputs
* ``Mn``, ``Mw``, ``PDI``
* validation error/warning count

Simulation
----------

``Simulation`` tab에서는 기본 반응기와 solver 조건을 설정한다.

* reactor: ``Batch``, ``Semi-batch``, ``CSTR``, ``Cascade``, ``PFR``
* backend: discrete, projected Galerkin, direct Galerkin
* integration time, output points, tolerance
* heat balance와 profile output

긴 실행은 ``SimulationWorker`` 를 통해 GUI thread와 분리된다. ``Stop`` 요청은 solver loop에서
stop flag를 확인하는 방식으로 처리된다.

MWD Viewer
----------

``MWD Viewer`` 는 molecular weight distribution을 분석하는 핵심 화면이다.

지원 기능:

* mole fraction / weight fraction toggle
* chain length / molecular weight / log molecular weight axis
* GPC convolution toggle
* time slider로 transient distribution 탐색
* 이전 실행 결과와 benchmark/reference overlay
* moment table
* CSV, PNG, PDF export

Model Builder
-------------

``Model Builder`` 는 reaction step과 template 기반 multi-step 모델을 다룬다.

* reaction step 추가/삭제
* enabled flag
* reaction kind, site, reactants, products
* rate expression과 generic parameter binding
* RAFT, NMP, ATRP, condensation, polyurethane, polyester, Ziegler-Natta 계열 template

Recipe Editor
-------------

``Recipe Editor`` 는 공정 recipe를 table 형태로 편집한다.

* initial conditions
* feed stream과 multiple feed tanks
* polymer feed
* integration control
* temperature/pressure profile
* pre-schedule: feed rate, temperature, pressure, residence time, coolant temperature, additional heat

Fitting
-------

``Fitting`` tab은 실험 데이터와 모델 output을 매핑하고 parameter estimation을 수행한다.

* CSV experiment import
* trimming window
* model output과 observation column mapping
* local least-squares
* differential evolution, dual annealing
* Bayesian sampling
* multi-experiment shared parameter fitting
* covariance, correlation, condition number, confidence interval, essential direction diagnostics

Script
------

``Script`` tab은 user-defined output을 정의한다.

지원되는 안전한 subset:

* scalar expression
* assignment
* ``for`` / ``range`` loop
* list/tuple indexing
* augmented assignment

임의의 ``exec`` 나 unsafe attribute access는 허용하지 않는다.
