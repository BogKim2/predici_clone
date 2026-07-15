PREDICI Clone Manual
====================

이 문서는 ``predici_clone`` 프로그램의 설치, 실행, GUI 사용법, 프로젝트 구조, API 사용법,
검증 및 배포 절차를 설명한다. 대상 독자는 polymer kinetics 연구자, 반응기 공정 엔지니어,
그리고 코드를 확장하려는 개발자이다.

.. note::

   이 프로젝트는 PREDICI 스타일의 연구/검증용 구현체이다. 상용 PREDICI 파일 포맷이나
   내부 알고리즘을 복제하지 않고, 공개적인 Python/SciPy/PySide6 기반 구조로 유사한 문제
   영역을 다룬다.

목차
----

.. toctree::
   :maxdepth: 2
   :caption: 사용자 문서

   installation
   quickstart
   tutorials
   gui
   projects
   outputs
   fitting
   packaging

.. toctree::
   :maxdepth: 2
   :caption: 개발자 문서

   architecture
   api
   validation
   extending
   glossary

빠른 명령
---------

.. code-block:: powershell

   python -m pip install -e .
   python -m predici_clone.app.main
   python -m pytest -q

Windows 실행 파일 빌드는 다음 명령으로 확인한다.

.. code-block:: powershell

   pyinstaller --noconfirm packaging\pyinstaller_predici_clone.spec
   .\dist\PrediciClone\PrediciClone.exe --smoke
