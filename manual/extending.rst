확장 가이드
===========

새 Reactor 추가
---------------

1. ``predici_clone/reactor`` 에 reactor class를 추가한다.
2. ``ReactorConfig.kind`` 와 validation을 확장한다.
3. ``SimulationEngine._build_reactor`` 에 dispatch를 추가한다.
4. recipe/profile/pre-schedule coupling이 필요한지 확인한다.
5. reactor unit test와 engine integration test를 추가한다.

새 Generic Output 추가
----------------------

1. ``postprocess/generic_outputs.py`` 에 provider를 추가한다.
2. ``OutputConfig.enabled_generic_outputs`` 에서 사용할 이름을 문서화한다.
3. GUI dashboard와 export에서 표시가 필요한지 확인한다.
4. output test를 추가한다.

새 Reaction Step 추가
---------------------

1. ``kinetics/reaction.py`` 의 enum/step schema를 확장한다.
2. ``kinetics/rate_terms.py`` 에 distribution RHS 효과를 추가한다.
3. 필요하면 ``kinetics/templates.py`` 에 template을 추가한다.
4. reaction DSL test와 engine regression test를 추가한다.

새 GUI 기능 추가
----------------

GUI 변경은 다음 원칙을 따른다.

* 계산 로직은 ``app`` 밖의 API/engine/postprocess에 둔다.
* GUI는 project snapshot을 만들고 worker에 전달한다.
* text label, unit, validation state를 명확히 표시한다.
* offscreen GUI test를 추가한다.

문서 업데이트
-------------

기능을 추가하면 이 ``manual`` 과 ``docs/plan3_progress.md`` 의 관련 항목을 갱신한다.
