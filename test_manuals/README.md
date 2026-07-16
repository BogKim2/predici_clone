# Manual Reproduction Suite

이 디렉터리는 39개 PREDICI/Presto-Kinetics 기능 문서에 대응하는 headless 실행 시나리오,
필터/실행기, HTML/Markdown/JSON/CSV 보고서 생성기를 포함합니다. 구현 기준은
루트 `plan6.md`의 M58b입니다.

## 가장 빠른 실행 방법

저장소 루트에서 다음 명령을 실행합니다.

```powershell
# 저장소 루트에서 실행
python -m pip install -e .
python -m test_manuals --list
python -m test_manuals --smoke
python -m test_manuals --all
python -m test_manuals --all --split --output .\test_manual_result
```

기본 결과는 다음 위치에 생성됩니다.

```text
test_manuals/outputs/README.md
test_manuals/outputs/input.json
test_manuals/outputs/report.html
test_manuals/outputs/result.md
test_manuals/outputs/result.json
test_manuals/outputs/result.csv
test_manuals/outputs/summary.png
```

```powershell
Start-Process .\test_manuals\outputs\report.html
Get-Content -Encoding utf8 .\test_manuals\outputs\result.md
Get-Content .\test_manuals\outputs\result.json -Raw | ConvertFrom-Json
Import-Csv .\test_manuals\outputs\result.csv
```

## 선택 옵션

```powershell
python -m test_manuals --pdf "PrediciPSD_Tutorial_2017"
python -m test_manuals --feature montecarlo
python -m test_manuals --milestone M42
python -m test_manuals --list --feature thermo
python -m test_manuals --all --output .\artifacts\manual-suite
```

- `--pdf`: PDF 파일명 부분 문자열, 대소문자 무시
- `--feature`: 등록된 feature와 정확히 일치
- `--milestone`: 등록된 milestone과 정확히 일치
- `--smoke`: fast 시나리오만 실행
- `--split`: 선택된 시나리오별로 `1`, `2`, ... 번호 폴더와 독립 실행 파일 생성
- `--output`: 보고서 저장 폴더 변경

필터는 함께 지정할 수 있으며 AND 조건으로 적용됩니다. 사용 가능한 값은 `--list`로 확인합니다.

## 결과 판정

- `PASS`: 모든 수치 지표가 정의된 기대 범위 안에 있음
- `FAIL`: 지표 누락/비유한 값/범위 이탈/실행 예외 발생
- 종료 코드 `0`: 전체 통과
- 종료 코드 `1`: 하나 이상 실패
- 종료 코드 `2`: 잘못된 CLI 사용

HTML과 Markdown 보고서는 기능·마일스톤 집계, PDF별 지표, 기대 범위, 실패 사유를 포함합니다.
`input.json`은 시나리오 입력과 기대 범위, `result.json`은 실행 명령과 환경을 포함한 구조화 결과,
`result.csv`는 PDF당 한 행을 기록합니다. 출력 폴더의 README에는 결과 요약, 결과 그림, 파일 색인,
39개 PDF 매핑이 생성됩니다. 동일한 출력 폴더를 사용하면 최신 결과로 덮어씁니다.

## 현재 전체 실행 결과

2026-07-16에 다음 명령으로 39개 시나리오를 모두 다시 실행했습니다.

```powershell
python -m test_manuals --all --split --output .\test_manual_result
```

결과는 `PASS 39 / FAIL 0 / SKIP 0`, PDF 커버리지는 `39 / 39 (100%)`입니다. 전체 PDF와
시나리오 매핑 및 개별 수치는 [test_manual_result/README.md](../test_manual_result/README.md)와
같은 폴더의 상세 보고서에서 확인할 수 있습니다.

`test_manual_result/1`부터 `test_manual_result/39`까지 각 폴더에는 입력 파일, 해당 테스트만
다시 실행하는 번호별 Python 프로그램, 구조화 결과, 보고서, 결과 그림이 있습니다. 예를 들어
1번 테스트는 다음과 같이 실행합니다.

```powershell
python .\test_manual_result\1\main_program1.py
```

프로그램은 같은 폴더의 `input.json`을 읽고 `result.json`, `result.md`, `result.csv`,
`report.html`, `result.png`, `README.md`를 갱신합니다. 번호별 PDF 매핑은
[전체 결과 색인](../test_manual_result/README.md#개별-테스트-폴더)에 있습니다.

## 파일 구조

- `registry.py`: `ManualExample`과 등록소
- `runner.py`: 필터, 실행, 기대값 검증
- `report.py`: 입력/결과 파일, HTML/Markdown/CSV, PNG 그림 및 결과 README 출력
- `cli.py`, `__main__.py`: CLI 진입점
- `examples/catalog.py`: 39개 출처와 재현 시나리오 매핑
- `outputs/`: 기본 결과 폴더. 생성 보고서는 Git에서 제외

39개 출처에는 `datas/`의 기능 문서와 루트의 Overview/Maxwell 문서가 포함됩니다.
`ListOfDocuments.pdf`는 색인이므로 제외하고, 중복된 `Predici11_Tutorials.pdf`는 한 번만 계산합니다.

전체 사용자 안내와 CI 예시는 루트 [README.md](../README.md) 및
[manual/manual_suite.rst](../manual/manual_suite.rst)에 있습니다.
