Tutorial Workflows
==================

Polyethylene Basic Project
--------------------------

``examples/tutorial_polyethylene_basic.py`` 는 tutorial PDF의 basic polyethylene 흐름을
재현하기 위한 최소 프로젝트를 실행한다.

.. code-block:: powershell

   python examples\tutorial_polyethylene_basic.py

동일한 프로젝트는 Python API에서도 생성할 수 있다.

.. code-block:: python

   from predici_clone.engine import SimulationEngine
   from predici_clone.validation.tutorial_projects import polyethylene_basic_project

   project = polyethylene_basic_project()
   result = SimulationEngine(project).run()
   print(result.final_moments.mn, result.final_moments.mw)

Oregonator / General Kinetics
-----------------------------

``examples/tutorial_oregonator.py`` 는 PRESTO-KINETICS 스타일의 general kinetic step을
검증한다. 특히 stoichiometric coefficient와 reaction order가 서로 다를 수 있음을 보여준다.

.. code-block:: powershell

   python examples\tutorial_oregonator.py

Run Control
-----------

run-to-time과 single-step API는 GUI의 ``Proc`` 및 ``1 Step`` 버튼과 같은 흐름을 위한
엔진 레벨 API이다.

.. code-block:: python

   from predici_clone.engine import SimulationEngine
   from predici_clone.validation.tutorial_projects import polyethylene_basic_project

   engine = SimulationEngine(polyethylene_basic_project())
   early = engine.run_to_time(0.1)
   one_step = engine.single_step()
   final = engine.run_to_time(engine.project.recipe.integration.t_final)

   print(early.metadata["run_control"])
   print(final.metadata["actual_values"][-1])

Script and Reaction Modifier Helpers
------------------------------------

PREDICI-style script helper functions are available through a safe command namespace.

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
