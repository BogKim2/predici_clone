패키징
======

Windows PyInstaller Build
-------------------------

.. code-block:: powershell

   pyinstaller --noconfirm packaging\pyinstaller_predici_clone.spec

결과물:

.. code-block:: text

   dist/
     PrediciClone/
       PrediciClone.exe

Smoke Test
----------

.. code-block:: powershell

   .\dist\PrediciClone\PrediciClone.exe --smoke

``--smoke`` 는 offscreen GUI를 시작하고 기본 simulation을 실행한 뒤 결과 manifest export까지 확인한다.

Packaging Files
---------------

* ``packaging/pyinstaller_predici_clone.spec``
* ``packaging/README.md``
* ``predici_clone/api/packaging_smoke.py``
* ``tests/test_packaging_files.py``

주의 사항
---------

PyInstaller 빌드 중 환경에 설치된 선택적 패키지 때문에 CUDA/TBB 등 경고가 출력될 수 있다. 현재 검증 기준은
빌드 exit code, packaging smoke, 그리고 ``PrediciClone.exe --smoke`` 통과 여부이다.
