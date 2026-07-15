Manual Reproduction Suite
=========================

개요
----

``test_manuals/`` 는 PREDICI/Presto-Kinetics 관련 39개 기능 문서에 대응하는 재현 시나리오를
headless 모드로 실행한다. ``plan6.md`` M58b를 구현 기준으로 사용하며, GUI를 열지 않고 각
시나리오의 수치 지표를 기대 범위와 비교한 뒤 HTML, Markdown, JSON, CSV 보고서를 생성한다.

39개 출처를 계산할 때 ``ListOfDocuments.pdf`` 는 문서 색인이므로 제외하며, 루트의
``Predici11_Tutorials.pdf`` 는 ``datas/`` 의 동명 파일과 중복되므로 하나의 시나리오로 계산한다.
PDF는 출처 메타데이터이며 실행 시 PDF 내용을 다시 읽지는 않는다.

실행 전 준비
------------

Python 3.11 이상이 필요하다. 모든 명령은 저장소 루트에서 실행한다.

.. code-block:: powershell

   cd F:\03llm\303predici
   python -m pip install -e .
   python -m test_manuals --help

설치하지 않고 다른 디렉터리에서 실행하면 ``No module named test_manuals`` 가 발생할 수 있다.
이 경우 저장소 루트로 이동하거나 editable 설치를 다시 수행한다.

등록 시나리오 확인
------------------

.. code-block:: powershell

   python -m test_manuals --list

출력의 각 행은 다음 네 필드로 구성된다.

.. list-table:: ``--list`` 출력 필드
   :header-rows: 1

   * - 필드
     - 설명
   * - ID
     - CLI와 레지스트리에서 사용하는 고유 시나리오 식별자
   * - Source PDF
     - 기능의 출처 문서 파일명
   * - Feature
     - ``montecarlo``, ``thermo``, ``psd`` 같은 기능 분류
   * - Milestone
     - ``M41`` 부터 ``M58`` 사이의 plan6 구현 단계

마지막 줄의 ``PDF coverage = 39 / 39 (100%)`` 는 39개 출처가 모두 하나 이상의 시나리오로
등록되었음을 의미한다.

빠른 확인과 전체 실행
---------------------

빠른 점검에서는 ``speed=fast`` 로 등록된 시나리오만 선택한다.

.. code-block:: powershell

   python -m test_manuals --smoke

전체 재현 보고서는 다음 명령으로 생성한다.

.. code-block:: powershell

   python -m test_manuals --all

저장소에 검증 결과를 정리할 때는 출력 폴더를 명시한다.

.. code-block:: powershell

   python -m test_manuals --all --split --output .\test_manual_result

정상 실행 예시는 다음과 같다.

.. code-block:: text

   PASS 39 / FAIL 0 / SKIP 0 - test_manuals\outputs\report.html

선택 실행
---------

PDF 필터는 파일명 부분 문자열이며 대소문자를 구분하지 않는다.

.. code-block:: powershell

   python -m test_manuals --pdf "PrediciPSD_Tutorial_2017"

Feature와 milestone은 등록값과 정확히 일치해야 한다.

.. code-block:: powershell

   python -m test_manuals --feature montecarlo
   python -m test_manuals --milestone M42

필터는 AND 조건으로 조합할 수 있다. 다음 명령은 M42에 속한 Monte Carlo 시나리오만 실행한다.

.. code-block:: powershell

   python -m test_manuals --feature montecarlo --milestone M42

실행 전에 선택 결과만 확인하려면 ``--list`` 와 필터를 함께 사용한다.

.. code-block:: powershell

   python -m test_manuals --list --feature thermo
   python -m test_manuals --list --milestone M44

사용 가능한 feature와 milestone은 항상 현재 ``--list`` 출력에서 확인한다.

결과 저장 위치
--------------

기본 출력 경로에는 다음 다섯 파일이 생성된다.

.. code-block:: text

   test_manuals/outputs/README.md
   test_manuals/outputs/report.html
   test_manuals/outputs/report.md
   test_manuals/outputs/results.json
   test_manuals/outputs/results.csv

``report.html`` 은 다음 정보를 포함한다.

* feature 및 milestone별 예제/PDF/PASS/FAIL/SKIP 집계
* 출처 PDF와 시나리오 제목, PASS/FAIL 상태, 실행 시간
* 계산된 수치 지표와 기대 최소/최대 범위
* 실패한 경우 예외 또는 범위 이탈 사유

``report.md`` 는 같은 상세 정보를 GitHub와 터미널에서 읽을 수 있게 제공한다. ``results.json`` 은
실행 명령, UTC 생성 시각, Python/플랫폼, 집계, 모든 개별 결과를 포함한다. ``results.csv`` 는
PDF당 한 행이며 Excel에서 열기 쉬운 UTF-8 BOM 형식이다. 출력 ``README.md`` 는 요약과 파일
색인, PDF-시나리오 매핑을 제공한다. 같은 출력 폴더로 다시 실행하면 다섯 파일을 최신 결과로
덮어쓴다.

PowerShell에서 보고서를 확인하는 명령은 다음과 같다.

.. code-block:: powershell

   Start-Process .\test_manuals\outputs\report.html
   Get-Content -Encoding utf8 .\test_manuals\outputs\report.md
   $result = Get-Content .\test_manuals\outputs\results.json -Raw | ConvertFrom-Json
   $result.summary
   Import-Csv .\test_manuals\outputs\results.csv | Format-Table source_pdf,status,metrics

결과를 별도 디렉터리에 보존하려면 ``--output`` 을 지정한다.

.. code-block:: powershell

   python -m test_manuals --all --output .\artifacts\manual-suite
   Start-Process .\artifacts\manual-suite\report.html

상대 경로는 저장소 루트를 기준으로 해석된다. 출력 디렉터리가 없으면 자동으로 생성된다.

2026-07-15 전체 실행 결과
-------------------------

저장소의 ``test_manual_result/`` 는 다음 명령으로 생성한 전체 결과를 포함한다.

.. code-block:: powershell

   python -m test_manuals --all --split --output .\test_manual_result

실행 결과는 ``PASS 39 / FAIL 0 / SKIP 0`` 이고 PDF 커버리지는 ``39 / 39 (100%)`` 이다.
``test_manual_result/README.md`` 에 39개 PDF와 시나리오의 전체 매핑이 있으며, 상세 수치와 기대
범위는 ``report.html`` 또는 ``report.md`` 에서, 자동 후처리용 원본은 ``results.json`` 과
``results.csv`` 에서 확인한다.

``--split`` 은 선택된 시나리오 순서대로 ``1`` , ``2`` , ... 번호 폴더를 만든다. 전체 실행에서는
``test_manual_result/1`` 부터 ``test_manual_result/39`` 까지 생성되며 각 폴더는 다음 일곱
파일을 포함한다.

.. code-block:: text

   test_manual_result/1/
     run_test.ps1
     run_test.cmd
     README.md
     report.html
     report.md
     results.json
     results.csv

``run_test.ps1`` 과 ``run_test.cmd`` 는 저장소 루트로 이동한 뒤 해당 폴더에 매핑된 PDF 한 건만
실행한다. 성공하면 같은 폴더의 결과 다섯 개를 갱신하고 HTML 보고서를 연다. 1번 테스트를 다시
실행하는 예시는 다음과 같다.

.. code-block:: powershell

   & .\test_manual_result\1\run_test.ps1

PowerShell 실행 정책 때문에 ``.ps1`` 실행이 차단되면 현재 명령에만 우회를 적용하거나 CMD 파일을
사용한다.

.. code-block:: powershell

   powershell -ExecutionPolicy Bypass -File .\test_manual_result\1\run_test.ps1
   .\test_manual_result\1\run_test.cmd

자동화에서 HTML을 열지 않으려면 PowerShell 실행 파일에 ``-NoOpen`` 을 추가한다.

.. code-block:: powershell

   powershell -ExecutionPolicy Bypass -File .\test_manual_result\1\run_test.ps1 -NoOpen

번호별 PDF, example ID, feature, milestone, 상태는 ``test_manual_result/README.md`` 의
**개별 테스트 폴더** 표에서 확인한다. 실행 파일에는 Python 3.11 이상과 프로젝트 의존성 설치가
필요하다.

판정 규칙
---------

각 ``ManualExample`` 은 ``expected`` 에 지표별 최소/최대 범위를 정의한다.

* **PASS**: 모든 지표가 존재하고 유한하며 허용 범위 안에 있다.
* **FAIL**: 지표가 없거나 NaN/무한대이거나 허용 범위를 벗어나거나 실행 예외가 발생했다.
* **SKIP**: 보고서 형식에 예약된 상태다. 현재 v2.0 레지스트리의 39개 시나리오는 모두 실행된다.

HTML 보고서의 ``Metrics`` 와 ``Reason`` 열에서 실제 지표와 실패 사유를 확인할 수 있다.

종료 코드와 CI 사용
-------------------

.. list-table:: 종료 코드
   :header-rows: 1

   * - 코드
     - 의미
   * - 0
     - 선택한 시나리오가 모두 통과했거나 ``--list`` 가 정상 완료됨
   * - 1
     - 하나 이상의 시나리오가 FAIL
   * - 2
     - 실행 선택 누락 또는 잘못된 CLI 인자

PowerShell 빌드에서 실패를 즉시 전파하는 예시는 다음과 같다.

.. code-block:: powershell

   python -m test_manuals --smoke --output .\artifacts\manual-smoke
   if ($LASTEXITCODE -ne 0) {
       throw "Manual reproduction suite failed: $LASTEXITCODE"
   }

전체 실행 결과를 CI artifact로 보관하려면 다음과 같이 별도 폴더를 사용한다.

.. code-block:: powershell

   python -m test_manuals --all --output .\artifacts\manual-full
   if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

문제 해결
---------

``No module named test_manuals``
   저장소 루트에서 실행 중인지 확인하고 ``python -m pip install -e .`` 을 다시 수행한다.

``select --all ...`` 오류
   옵션 없이 실행했다. ``--all`` , ``--smoke`` , ``--pdf`` , ``--feature`` , ``--milestone`` ,
   ``--list`` 중 하나를 지정한다.

선택된 시나리오가 없음
   feature/milestone은 정확히 일치해야 한다. ``--list`` 와 같은 필터를 함께 사용해 선택 결과를
   먼저 확인한다.

보고서 파일을 쓸 수 없음
   쓰기 권한이 있는 위치를 ``--output`` 으로 지정한다.

구조와 확장
-----------

주요 파일의 역할은 다음과 같다.

.. list-table:: ``test_manuals`` 구성
   :header-rows: 1

   * - 파일
     - 역할
   * - ``registry.py``
     - ``ManualExample`` 데이터 구조와 시나리오 등록
   * - ``runner.py``
     - 필터 선택, 실행, 지표 검증, PASS/FAIL 결과 생성
   * - ``report.py``
     - HTML/Markdown/JSON/CSV 보고서와 결과 README 작성
   * - ``cli.py`` / ``__main__.py``
     - ``python -m test_manuals`` 명령 진입점
   * - ``examples/catalog.py``
     - 39개 PDF 매핑과 기능별 재현 함수
   * - ``outputs/``
     - 기본 보고서 출력 위치. 생성 보고서는 Git에서 제외됨

새 시나리오는 고유 ID, 출처 PDF, feature, milestone, 실행 함수, 기대 지표 범위를 지정해
레지스트리에 등록한다. 등록 무결성과 CLI/report 동작은 ``tests/test_manual_suite.py`` 에서 검증한다.
