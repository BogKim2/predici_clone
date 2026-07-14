검증과 Benchmark
================

테스트 실행
-----------

.. code-block:: powershell

   python -m pytest -q

주요 테스트 범위:

* project schema roundtrip
* SimulationEngine callbacks
* reactor models
* Galerkin operators and backend
* reaction DSL and templates
* GPC/output/report generation
* GUI smoke and GUI workflow
* fitting and sensitivity
* automation/interoperability
* PyInstaller packaging smoke

Benchmark Cases
---------------

``predici_clone.validation.paper_benchmarks`` 는 문헌/합성 benchmark case를 제공한다.

대표 benchmark:

* Flory-Schulz analytic distribution
* Fogler fractionation example
* multi-site Schulz-Flory synthetic benchmark
* discrete/Galerkin comparison
* GPC convolution checks

검증 원칙
---------

* synthetic data는 synthetic임을 명시한다.
* 공개 자료와 재현 가능한 수식 기반 benchmark를 우선한다.
* figure digitization은 license와 metadata를 확인한 경우에만 별도 관리한다.
* GUI는 offscreen smoke와 workflow test로 회귀를 막는다.

수동 확인 포인트
----------------

* GUI 기본 창에서 text overlap이 없는지 확인
* Batch, Semi-batch, CSTR, Cascade, PFR 실행 가능 여부
* MWD Viewer의 mode/axis/GPC/overlay/time slider 확인
* result export와 project save/load 확인
