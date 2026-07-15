# predici_clone v2.0

PREDICI 스타일의 고분자 반응 시뮬레이션 프로그램입니다. PySide6 데스크톱 GUI와 함께
결정론적/Hybrid Monte Carlo 반응 해석, PSD/PBE, 에멀전 및 다상 반응기, Peng-Robinson
열역학, 파라미터 추정, replay, 자동화 및 상호운용 기능을 제공합니다.

## 설치

Windows PowerShell에서 저장소 루트로 이동한 뒤 editable 모드로 설치합니다.

```powershell
cd F:\03llm\303predici
python -m pip install -e .
```

Python 3.11 이상이 필요하며 NumPy, SciPy, Matplotlib, pandas, PySide6, openpyxl,
networkx가 함께 설치됩니다.

## GUI 실행

```powershell
python -m predici_clone.app.main
```

## 테스트

전체 자동화 테스트는 다음과 같이 실행합니다.

```powershell
python -m pytest -q
```

v2.0 릴리스 기준 결과와 벤치마크는 [docs/v2_ci_report.md](docs/v2_ci_report.md)와
[docs/v2_benchmark_report.md](docs/v2_benchmark_report.md)에 기록되어 있습니다.

## 매뉴얼 빌드

Sphinx 매뉴얼 소스는 `manual/`에 있습니다.

```powershell
python -m pip install -r manual\requirements.txt
sphinx-build -b html -W manual manual\_build\html
Start-Process .\manual\_build\html\index.html
```

`-W`는 Sphinx 경고를 빌드 실패로 처리합니다. Manual Reproduction Suite의 상세 사용법은
빌드된 매뉴얼의 **Manual Reproduction Suite** 장과
[manual/manual_suite.rst](manual/manual_suite.rst)에서 확인할 수 있습니다.

## Manual Reproduction Suite

`test_manuals/`는 39개 기능 문서에 대응하는 headless 재현 시나리오를 등록하고 실행합니다.
GUI를 열지 않으며, 시나리오별 상태와 수치 지표를 HTML/Markdown 보고서로 만듭니다.

### 1. 실행 준비

모든 명령은 저장소 루트에서 실행합니다.

```powershell
cd F:\03llm\303predici
python -m pip install -e .
python -m test_manuals --help
```

PDF 파일은 시나리오의 출처 메타데이터입니다. 실행 코드는 PDF를 실시간으로 읽지 않으므로
보고서를 만들기 위해 PDF 뷰어가 필요하지 않습니다.

### 2. 등록 시나리오 확인

```powershell
python -m test_manuals --list
```

각 행은 `시나리오 ID`, `출처 PDF`, `feature`, `milestone` 순서입니다. 마지막 줄의
`PDF coverage = 39 / 39 (100%)`로 등록 범위를 확인할 수 있습니다.

### 3. 빠른 확인과 전체 실행

```powershell
# fast 등급 시나리오만 실행
python -m test_manuals --smoke

# 등록된 39개 시나리오 전체 실행
python -m test_manuals --all
```

정상 실행 시 콘솔에는 다음 형식의 요약이 표시됩니다.

```text
PASS 39 / FAIL 0 / SKIP 0 - test_manuals\outputs\report.html
```

### 4. 원하는 항목만 실행

```powershell
# PDF 파일명의 일부로 선택: 대소문자를 구분하지 않음
python -m test_manuals --pdf "PrediciPSD_Tutorial_2017"

# feature 이름은 정확히 일치해야 함
python -m test_manuals --feature montecarlo

# milestone 이름은 정확히 일치해야 함
python -m test_manuals --milestone M42

# 필터 조합도 가능
python -m test_manuals --feature montecarlo --milestone M42

# 필터 결과를 실행하지 않고 먼저 확인
python -m test_manuals --list --feature thermo
```

사용 가능한 feature/milestone 값은 `--list` 결과를 기준으로 선택하는 것이 가장 정확합니다.

### 5. 결과 폴더와 보고서 확인

기본 출력 위치는 다음과 같습니다.

```text
test_manuals/outputs/report.html
test_manuals/outputs/report.md
```

- `report.html`: PDF, 시나리오, PASS/FAIL 상태, 실행 시간, 수치 지표, 실패 사유를 포함합니다.
- `report.md`: 전체 상태 요약과 PDF별 실행 결과를 표 형태로 기록합니다.
- 같은 출력 폴더로 다시 실행하면 두 보고서 파일을 최신 결과로 덮어씁니다.

PowerShell에서 결과를 여는 방법:

```powershell
Start-Process .\test_manuals\outputs\report.html
Get-Content -Encoding utf8 .\test_manuals\outputs\report.md
```

별도 폴더에 결과를 보관하려면 `--output`을 사용합니다.

```powershell
python -m test_manuals --all --output .\artifacts\manual-suite
Start-Process .\artifacts\manual-suite\report.html
```

### 6. 판정과 종료 코드

- `PASS`: 모든 기대 지표가 정의된 최소/최대 범위 안에 있습니다.
- `FAIL`: 지표 누락, NaN/무한대, 허용 범위 이탈 또는 실행 중 예외가 발생했습니다.
- `SKIP`: 보고서 형식에 예약된 상태입니다. 현재 등록된 v2.0 시나리오는 모두 실행 대상입니다.
- 종료 코드 `0`: 선택된 시나리오가 모두 통과했습니다.
- 종료 코드 `1`: 하나 이상의 시나리오가 실패했습니다.
- 종료 코드 `2`: 필수 실행 선택이 없거나 CLI 인자가 잘못되었습니다.

PowerShell/CI에서 종료 코드를 확인할 수 있습니다.

```powershell
python -m test_manuals --smoke --output .\artifacts\manual-smoke
if ($LASTEXITCODE -ne 0) { throw "Manual suite failed: $LASTEXITCODE" }
```

### 7. 문제 해결

- `No module named test_manuals`: 저장소 루트인지 확인하고 `python -m pip install -e .`을 다시 실행합니다.
- `select --all ...`: 옵션 없이 실행한 경우입니다. `--all`, `--smoke`, `--pdf`, `--feature`,
  `--milestone`, `--list` 중 하나를 지정합니다.
- 빈 보고서: 필터 값이 등록값과 일치하지 않을 수 있습니다. `--list`로 값을 확인합니다.
- 보고서 쓰기 실패: `--output`으로 쓰기 가능한 디렉터리를 지정합니다.

세부 구조와 시나리오 등록 방법은 [test_manuals/README.md](test_manuals/README.md)를 참고하십시오.

## Windows 실행 파일 빌드

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --clean packaging\pyinstaller_predici_clone.spec
.\dist\PrediciClone\PrediciClone.exe --smoke
```

v2.0 전체 패키징 확인은 다음 스크립트로 실행합니다.

```powershell
.\scripts\packaging_smoke_test_v2.ps1
```

구현 범위는 [plan6.md](plan6.md), 변경 내역은 [CHANGELOG.md](CHANGELOG.md)를 참고하십시오.
