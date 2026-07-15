빠른 시작
=========

GUI로 기본 시뮬레이션 실행
--------------------------

1. ``python -m predici_clone.app.main`` 을 실행한다.
2. 상단 툴바에서 ``Run`` 을 누른다.
3. ``Dashboard`` 에서 주요 scalar output을 확인한다.
4. ``MWD Viewer`` 에서 분자량 분포, moment table, overlay를 확인한다.
5. ``File`` 메뉴 또는 툴바에서 프로젝트와 결과를 저장한다.

Python API로 실행
-----------------

.. code-block:: python

   from predici_clone.api import IntegrationControl, Project, ReactorConfig, Recipe
   from predici_clone.engine import SimulationEngine

   project = Project(
       reactor=ReactorConfig(kind="Batch", nmax=80),
       recipe=Recipe(integration=IntegrationControl(t_final=10.0, output_points=50)),
   )
   result = SimulationEngine(project).run()

   print(result.success)
   print(result.final_moments.mn, result.final_moments.mw, result.final_moments.pdi)

프로젝트 저장과 로드
--------------------

.. code-block:: python

   from pathlib import Path
   from predici_clone.api import load_project, save_project

   save_project(project, Path("project.predici.json"))
   loaded = load_project(Path("project.predici.json"))

예제 실행
---------

.. code-block:: powershell

   python examples\industrial_semibatch_cstr.py
   python examples\tutorial_polyethylene_basic.py
   python examples\tutorial_oregonator.py

첫 번째 예제는 semi-batch와 CSTR 조건을 비교하고 ``Mn``, ``Mw``, ``PDI`` 를 출력한다.
두 tutorial 예제는 polyethylene basic workflow와 Oregonator general kinetic workflow를
각각 검증한다.
