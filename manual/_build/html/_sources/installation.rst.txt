설치
====

요구 사항
---------

* Python 3.11 이상
* Windows 환경 권장
* 주요 Python 패키지: ``numpy``, ``scipy``, ``matplotlib``, ``pandas``, ``PySide6``
* 문서 빌드용: ``sphinx``

개발 모드 설치
--------------

저장소 루트에서 다음을 실행한다.

.. code-block:: powershell

   python -m pip install -e .

문서 빌드 도구가 없다면 추가로 설치한다.

.. code-block:: powershell

   python -m pip install sphinx

동작 확인
---------

.. code-block:: powershell

   python -m pytest -q
   python -m predici_clone.app.main --smoke

GUI 실행
--------

.. code-block:: powershell

   python -m predici_clone.app.main

문서 빌드
---------

.. code-block:: powershell

   sphinx-build -b html manual manual\_build\html

빌드된 문서는 ``manual\_build\html\index.html`` 에서 확인할 수 있다.
