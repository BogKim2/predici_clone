# Manual Reproduction Suite

이 디렉터리는 39개 PREDICI/Presto-Kinetics 기능 문서에 대응하는 headless 실행 시나리오,
필터/실행기, HTML/Markdown 보고서 생성기를 포함합니다.

## 가장 빠른 실행 방법

저장소 루트에서 다음 명령을 실행합니다.

```powershell
cd F:\03llm\303predici
python -m pip install -e .
python -m test_manuals --list
python -m test_manuals --smoke
python -m test_manuals --all
```

기본 결과는 다음 위치에 생성됩니다.

```text
test_manuals/outputs/report.html
test_manuals/outputs/report.md
```

```powershell
Start-Process .\test_manuals\outputs\report.html
Get-Content -Encoding utf8 .\test_manuals\outputs\report.md
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
- `--output`: 보고서 저장 폴더 변경

필터는 함께 지정할 수 있으며 AND 조건으로 적용됩니다. 사용 가능한 값은 `--list`로 확인합니다.

## 결과 판정

- `PASS`: 모든 수치 지표가 정의된 기대 범위 안에 있음
- `FAIL`: 지표 누락/비유한 값/범위 이탈/실행 예외 발생
- 종료 코드 `0`: 전체 통과
- 종료 코드 `1`: 하나 이상 실패
- 종료 코드 `2`: 잘못된 CLI 사용

HTML 보고서는 지표와 실패 사유까지 포함하고, Markdown 보고서는 실행 요약과 PDF별 상태를
제공합니다. 동일한 출력 폴더를 사용하면 보고서 파일은 최신 실행 결과로 덮어씁니다.

## 파일 구조

- `registry.py`: `ManualExample`과 등록소
- `runner.py`: 필터, 실행, 기대값 검증
- `report.py`: HTML/Markdown 출력
- `cli.py`, `__main__.py`: CLI 진입점
- `examples/catalog.py`: 39개 출처와 재현 시나리오 매핑
- `outputs/`: 기본 결과 폴더. 생성 보고서는 Git에서 제외

39개 출처에는 `datas/`의 기능 문서와 루트의 Overview/Maxwell 문서가 포함됩니다.
`ListOfDocuments.pdf`는 색인이므로 제외하고, 중복된 `Predici11_Tutorials.pdf`는 한 번만 계산합니다.

전체 사용자 안내와 CI 예시는 루트 [README.md](../README.md) 및
[manual/manual_suite.rst](../manual/manual_suite.rst)에 있습니다.
