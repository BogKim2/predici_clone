구조
====

패키지 개요
-----------

.. code-block:: text

   predici_clone/
     api/          project schema, IO, automation, validation
     app/          PySide6 GUI and worker thread
     core/         Galerkin basis, mesh, moment, adaptive tools
     engine/       SimulationEngine, SimulationResult, shooting
     integrator/   solver helpers and Jacobian utilities
     kinetics/     reaction DSL, templates, rate terms
     postprocess/  outputs, GPC, fitting, reports, sensitivity
     reactor/      Batch, Semi-batch, CSTR, Cascade, PFR, energy balance
     validation/   benchmark cases

Engine Boundary
---------------

GUI, tests, scripts는 직접 reactor를 호출하지 않고 :class:`predici_clone.engine.simulation_engine.SimulationEngine`
을 사용한다.

.. code-block:: python

   result = SimulationEngine(project).run()

``SimulationEngine`` 은 다음을 담당한다.

* project schema 해석
* reactor instance 구성
* discrete/Galerkin backend 선택
* recipe profile과 pre-schedule 적용
* heat balance coupling
* generic metadata와 output trajectory 구성

Backend
-------

지원 backend:

* ``discrete``: chain length vector 직접 적분
* ``galerkin``: discrete result를 Galerkin field로 projection/reconstruction
* ``galerkin_direct``: coefficient-space PBE system 적분

Reactor Models
--------------

* Batch
* Semi-batch
* CSTR
* CSTR Cascade
* PFR approximation via cascade/staged logic
* lumped heat balance and heat exchanger hooks

Reaction DSL
------------

``kinetics`` 패키지는 reaction step과 rate law를 정의한다.

대표 reaction kind:

* initiation
* propagation
* termination
* chain transfer
* branching
* scission
* PolymerPartition

GUI Boundary
------------

``app`` 은 PySide6 전용이다. 계산 로직은 ``engine`` 과 ``api`` 에 유지하여 CLI/API/test에서도 재사용한다.

``SimulationWorker`` 는 long-running simulation을 GUI thread와 분리하고 다음 signal을 제공한다.

* ``progress``
* ``step_done``
* ``finished``
* ``error``
* ``log``
