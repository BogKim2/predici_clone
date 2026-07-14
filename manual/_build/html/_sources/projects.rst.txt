프로젝트와 Recipe
=================

프로젝트 스키마
---------------

프로젝트의 중심 객체는 :class:`predici_clone.api.project_schema.Project` 이다.

주요 필드:

* ``schema_version``
* ``name``
* ``reactor``: :class:`predici_clone.api.project_schema.ReactorConfig`
* ``kinetics``: :class:`predici_clone.api.project_schema.FRPParameters`
* ``recipe``: :class:`predici_clone.api.project_schema.Recipe`
* ``outputs``: :class:`predici_clone.api.project_schema.OutputConfig`
* ``heat_balance``: :class:`predici_clone.api.project_schema.HeatBalanceConfig`
* ``reaction_steps``
* ``generic_parameters``

Recipe
------

``Recipe`` 는 simulation 조건을 묶는다.

* ``unit_system``
* ``initial``
* ``feed``
* ``feed_tanks``
* ``polymer_feed``
* ``integration``
* ``pre_schedule``
* ``temperature_profile``
* ``pressure_profile``
* ``shooting_control``

Pre-schedule 예시
-----------------

.. code-block:: python

   from predici_clone.api import Project, append_pre_schedule_step

   project = append_pre_schedule_step(
       Project(),
       time=5.0,
       action="set_feed_rate",
       value=0.12,
   )

저장 형식
---------

프로젝트는 JSON으로 저장한다.

.. code-block:: python

   from predici_clone.api import save_project, load_project

   save_project(project, "case.predici.json")
   loaded = load_project("case.predici.json")

결과 저장
---------

시뮬레이션 결과는 manifest와 array 파일로 저장한다.

.. code-block:: python

   from predici_clone.api import save_simulation_result

   manifest_path = save_simulation_result(result, "results/run_001")

저장되는 대표 파일:

* ``manifest.json``
* ``distribution_history.npz``
* final distribution CSV
* moment CSV
