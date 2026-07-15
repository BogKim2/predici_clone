Tutorial Workflows
==================

이 장은 ``Predici11_Tutorials.pdf`` 에서 요구한 작업 흐름을 현재 GUI와 Python API로
재현하는 절차를 정리한다. 상용 PREDICI 파일 포맷을 복제하지 않고, clone 내부의
프로젝트 스키마와 PySide6 GUI를 사용한다.

Polyethylene Basic Project
--------------------------

Python smoke workflow는 다음 명령으로 실행한다.

.. code-block:: powershell

   python examples\tutorial_polyethylene_basic.py

동일한 프로젝트는 API에서도 만들 수 있다.

.. code-block:: python

   from predici_clone.engine import SimulationEngine
   from predici_clone.validation.tutorial_projects import polyethylene_basic_project

   project = polyethylene_basic_project()
   result = SimulationEngine(project).run()
   print(result.final_moments.mn, result.final_moments.mw)

GUI에서 재현하려면 다음 순서로 진행한다.

1. ``python -m predici_clone.app.main`` 으로 GUI를 연다.
2. ``Simulation`` 탭에서 reactor, backend, final time을 설정한다.
3. ``Proc`` 로 짧은 시간까지 먼저 실행해 초기 conversion과 moment 변화를 확인한다.
4. ``1 Step`` 으로 한 step씩 진행하면서 ``Actual values`` 표의 step/time/stepsize를 확인한다.
5. ``MWD Viewer`` 에서 time slider, axis selector, GPC convolution, overlay를 확인한다.
6. ``Chart administration`` 표에서 page와 graph row를 저장해 chart 구성을 프로젝트에 남긴다.

Oregonator / General Kinetics
-----------------------------

PRESTO-KINETICS 스타일의 general kinetic workflow는 다음 예제로 검증한다.

.. code-block:: powershell

   python examples\tutorial_oregonator.py

핵심 검증 포인트는 stoichiometric coefficient와 reaction order가 독립적으로 저장되고
실행된다는 점이다.

.. code-block:: python

   from predici_clone.engine import SimulationEngine
   from predici_clone.validation.tutorial_projects import oregonator_kinetics_project

   project = oregonator_kinetics_project(corrected_order=True)
   result = SimulationEngine(project).run()
   print(result.metadata["final_concentrations"])

Component and PatternFinder Workflow
------------------------------------

``Components`` 탭은 Substance, polymer species, parameter를 직접 편집한다.

* Substance/polymer row에는 phase setting, density mode, linear density coefficients,
  heat-capacity coefficients가 포함된다.
* ``Apply Components`` 를 누르면 component admin API를 통해 프로젝트 스키마에 저장된다.
* Inspector는 validation error/warning row를 색으로 표시한다.

``Model Builder`` 탭은 PatternFinder-style catalog를 제공한다.

* catalog table에서 template의 category, kind, reactant slot, product slot, parameter slot을 확인한다.
* selector를 바꾸면 preview label에 ``reactants -> products`` 형태가 표시된다.
* ``Add Pattern`` 은 기본 slot binding으로 reaction step을 생성하고 필요한 species/parameter를 자동 선언한다.
* modifier 영역에서 ``GP_kp(File)`` 또는 ``GP_kp*File`` 을 선택하고 script를 입력하면
  선택된 reaction step에 modifier expression과 script가 저장된다.

Recipe Consistency Workflow
---------------------------

``Recipe Editor`` 탭의 consistency 영역은 tutorial의 ``Input as`` workflow를 지원한다.

지원 mode:

* ``absolute_mass``
* ``mass_part_total_mass``
* ``absolute_mole``
* ``mole_part``
* ``concentration_and_volume``
* ``mass_part_total_mole``
* ``mole_part_total_mass``

절차:

1. ``Add Consistency Row`` 로 component row를 만든다.
2. MW, density, mass/moles/concentration/parts 중 mode에 필요한 값을 입력한다.
3. ``Input as`` mode와 Volume/Mass/Moles basis를 설정한다.
4. ``Normalize Mode`` 를 눌러 mass, moles, concentration, mass part, mole part를 재계산한다.
5. ``Set concentration consistent`` 는 density consistency sum이 1이 되도록 target concentration을 조정한다.
6. ``Set Rest`` 는 target mass part를 나머지 값으로 채운다.

Consistency sum이 1에서 벗어나면 label과 table row가 warning 색으로 표시된다.

Run Control and Moments Mode
----------------------------

``Simulation`` 탭은 tutorial의 run-control 흐름을 GUI와 API 양쪽에서 제공한다.

.. code-block:: python

   from predici_clone.engine import SimulationEngine
   from predici_clone.validation.tutorial_projects import polyethylene_basic_project

   engine = SimulationEngine(polyethylene_basic_project())
   early = engine.run_to_time(0.1)
   one_step = engine.single_step()
   final = engine.run_to_time(engine.project.recipe.integration.t_final)

   print(early.metadata["run_control"])
   print(final.metadata["actual_values"][-1])

``simulation_mode="moments"`` 를 선택하면 result state는 ``M0``, ``M1``, ``M2``,
``Mn``, ``Mw``, ``PDI`` 로 축약된다. Distribution history는 chart reference 비교를 위해
계속 보존된다.

Script and Debug Workflow
-------------------------

``Script`` 탭은 user-defined output, function catalog, debugger trace를 한 곳에서 다룬다.

* ``Generate Template`` 은 현재 species/parameter를 기반으로 boilerplate script를 생성한다.
* ``Apply Scripted Outputs`` 는 output table의 script를 프로젝트에 저장한다.
* ``Debug scripts`` 표에 여러 script를 입력하고 ``Run Debug`` 를 누르면 line, assignment,
  value trace가 표시된다.

PREDICI-style helper functions는 safe command namespace에서 실행된다.

.. code-block:: python

   from predici_clone.postprocess.scripted_outputs import evaluate_expression
   from predici_clone.script import ScriptCommandState, script_command_namespace

   state = ScriptCommandState(current_concentrations={"M": 2.0}, parameters={"kp": 0.1})
   value = evaluate_expression('getkp("kp") * getco("M")', script_command_namespace(state))

Reaction coefficient modifiers support ``k(File)`` and ``k*File`` style expressions.

.. code-block:: python

   from predici_clone.script import ScriptCommandState, evaluate_modifier_expression

   state = ScriptCommandState(current_concentrations={"M": 2.0}, parameters={"kp": 0.1})
   scripts = {"File": 'result = getkp("kp") * getco("M")'}
   modified = evaluate_modifier_expression("kp(File)", scripts=scripts, state=state)

Chart and Reference Data
------------------------

The charting API separates display configuration, reference curve IO, and GPC-specific
weighting.

.. code-block:: python

   import numpy as np
   from predici_clone.postprocess.charting import ChartConfig, distribution_chart_profile

   profile = distribution_chart_profile(
       np.asarray([0.0, 2.0, 1.0]),
       ChartConfig(distribution_y_axis="gpc", x_axis_scale="logarithmic"),
   )

