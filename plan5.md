# PREDICI Clone 개발 계획 v5: Post-Tutorial Hardening, Reactor/PE Completion, GUI Modernization

이 문서는 `plan4_rev.md`(M22~M32, 튜토리얼 재현 범위)가 **완료된 이후** 진행할 다음 단계
계획이다. `plan3.md`에서 로드맵으로만 남아 있던 항목(M16 reactor 확장, M17~M19 fitting/
sensitivity/shooting, M21 packaging)과, `plan.md` 원안에서 "가장 어려운 부분"으로 후순위에
두었던 2차원(공중합) 분포, 그리고 이번에 `Predici11_Tutorials.pdf`의 스크린샷을 직접
rasterize하여 관찰한 **시각 디자인 패턴**을 반영한 GUI 현대화까지 하나의 계획으로 묶는다.

전제 조건: `plan4_rev.md`의 Completion Criteria(1~15번)가 모두 충족된 상태.

참조:

- `plan.md` (원 설계, 8절 리스크: 2D 분포는 "가장 어려운 부분, 후순위")
- `plan3.md` (M16~M21 로드맵, 아직 미착수)
- `plan4_rev.md` (M22~M32, 이 문서의 전제 조건)
- `Predici11_Tutorials.pdf` 스크린샷 rasterize 분석 (아래 0절)

---

## 0. 그림 분석에서 얻은 GUI 설계 시사점

`Predici11_Tutorials.pdf`의 주요 스크린샷(Reactor/Substance 다이얼로그, PatternFinder,
Graphs 창, Chart administration, Script debugger, Recipe consistency, GPC 아티팩트,
Oregonator 일반 kinetic step 표)을 150dpi로 rasterize해 직접 확인한 결과, 텍스트 추출만으로는
드러나지 않는 다음 시각적 패턴이 확인되었다.

| 관찰 | 원본 PREDICI 11 | Clone에 적용할 방향 |
| --- | --- | --- |
| 상호작용 구조 | 모달 다이얼로그가 3~4단으로 중첩(workshop → 카탈로그 → 편집 → 필드 팝업) | **비모달 인스펙터 패턴**으로 전환: 우측 dock에서 인라인 편집, 팝업은 선택 리스트류로만 최소화 (§M33) |
| 아이콘 언어 | 물질 종류(E/I/R(s)/P 등)마다 고정된 소형 컬러 아이콘이 팔레트/트리/패턴 미리보기에서 일관 재사용 | 동일한 "kind별 아이콘" 규칙을 `Substance.kind`/`PolymerSpecies` 스키마와 연결해 트리/드래그팔레트/차트 범례에서 재사용 (§M33) |
| 색상 규약 | 파랑=1차 곡선, 빨강=불일치 경고·2차(reference) 곡선 겸용, 노랑=편집가능 셀 | 규약을 분리: 빨강은 **오류/경고 전용**, reference 곡선은 별도 색(예: 주황 점선)으로 구분해 원본의 모호함을 개선 (§M33) |
| 리스트+툴바 패턴 | 모든 그리드 위에 동일한 소형 아이콘 툴바(추가/삭제/재정렬/복제) 반복 | 공용 `EditableTableWidget` 컴포넌트로 표준화해 전 GUI에서 재사용 (§M33) |
| GPC tail 아티팩트 | 실제 스크린샷에서 고분자량 tail이 0으로 완전히 떨어지지 않는 현상이 육안으로 확인됨 | `plan4_rev.md` M26에서 지적한 core-GUI 가중치 계약을 M34(core 정밀도 강화)에서 수치적으로 검증 |
| Debugger | 코드 라인 표 + 스크립트별 소형 탭 버튼, 편집은 별도 창으로 이동 | 비모달 dock 내 탭으로 유지하되, 편집은 같은 dock 안에서 인라인 전환(별도 창 최소화) |

이 표의 항목들은 아래 M33에서 구체화한다.

---

## 1. 이 단계의 목표

1. **Reactor/Process 완결성** — batch/semi-batch/CSTR을 넘어 PFR, cascade, 비등온
   (heat balance/heat exchanger)까지 `plan3.md` M16 로드맵을 완료한다.
2. **Parameter Estimation 완결성** — `plan3.md` M17~M19(로컬/글로벌 탐색, 민감도,
   shooting control)를 실제로 구현한다. 현재까지는 스키마/설계만 존재.
3. **2차원(공중합) 분포 지원** — `plan.md`가 후순위로 미룬 "가장 어려운 부분"에
   본격 착수한다. 조성 분포(composition distribution)를 사슬길이 분포와 결합한다.
4. **GUI 현대화** — 0절의 시각 분석을 바탕으로 모달 중첩을 줄이고 공용 위젯 라이브러리로
   전환한다.
5. **Interoperability 완결** — Excel/CSV 이외의 내보내기(NPZ, 선택적 Matlab/C moment
   식 export)와 automation API 스텁을 실제 함수로 구현한다.
6. **Packaging & Release** — Windows PyInstaller 빌드를 만들고 v1.0 릴리스 체크리스트를
   완료한다.

비목표(변경 없음): PREDICI 파일 포맷 리버스 엔지니어링, PREDICI UI 픽셀 복제, Cape-Open
전체 구현(장기 과제로 유지), Wingraphviz 등 외부 바이너리 의존(`plan4_rev.md` §8 유지).

---

## 2. Milestone Roadmap

| 단계 | 목표 | 주요 산출물 | 검증 |
| --- | --- | --- | --- |
| M33 | GUI Modernization (비모달 인스펙터, 공용 위젯, 아이콘/색상 규약) | `app/widgets/editable_table.py`, `app/widgets/species_icon.py`, 색상 토큰 정의 | 모달 깊이 회귀 테스트(최대 2단 이하), 시각 스모크 테스트 |
| M34 | Reactor 확장: PFR, cascade, heat balance/heat exchanger | `reactor/pfr.py`, `reactor/cascade.py`, `reactor/energy_balance.py` | PFR 해석해 비교, cascade→PFR 근사 수렴 테스트 |
| M35 | Parameter Estimation v1: 로컬/글로벌 탐색 | `fitting/local_search.py`(Gauss-Newton/LM), `fitting/global_search.py`(simulated annealing) | synthetic parameter recovery 벤치마크 |
| M36 | Sensitivity Analysis & Shooting Control | `fitting/sensitivity.py`(sigma-point, MC), `engine/shooting.py` | 민감도 벤치마크, shooting 목표 도달 테스트 |
| M37 | Copolymer 2D Distribution (composition x chain-length) | `core/basis_2d.py`, `kinetics/copolymer_terms.py` | 2D Flory 근사 대비 벤치마크 |
| M38 | Automation API & Export 완결 | `api/automation.py` 실구현, NPZ/Matlab export | automation API 계약 테스트 |
| M39 | Packaging & Release | PyInstaller 빌드, 릴리스 체크리스트 | clean-venv 빌드+실행 스모크 |
| M40 | v1.0 Regression Freeze | 전체 벤치마크/튜토리얼/GUI 스모크 통합 실행 문서 | `pytest -q` 전체 통과, 매뉴얼 빌드 |

---

## 3. Detailed Implementation Plan

### M33. GUI Modernization

#### Scope

0절 분석을 바탕으로 GUI의 상호작용 패턴과 공용 컴포넌트를 정리한다. 이 마일스톤은
신규 기능이 아니라 **기존 M9~M29에서 만들어진 화면들을 재사용 가능한 컴포넌트로
리팩터링**하는 작업이다.

#### Requirements

- **모달 깊이 축소**: 물질/파라미터/반응 스텝 편집을 별도 모달 대신 우측 Inspector dock
  안에서 인라인 폼으로 전환한다. PatternFinder처럼 탐색이 필요한 카탈로그류만 모달(또는
  중앙 탭)로 유지한다. 목표: 어떤 편집 흐름도 모달 2단을 넘지 않는다(원본은 최대 4단).
- **공용 위젯**:
  - `EditableTableWidget`: 추가/삭제/재정렬/복제 툴바 + 인라인 검증(빨간 텍스트) 표준화.
  - `SpeciesIconProvider`: `Substance.kind`/`PolymerSpecies` 종류별 고정 아이콘/색상을
    매핑하는 단일 소스. 트리, 드래그 팔레트, 차트 범례가 모두 이 provider를 사용한다.
- **색상 토큰 재정의** (원본의 "빨강 이중 의미" 문제 개선):
  - `color.error` (불일치/검증 실패 전용, 빨강)
  - `color.reference_curve` (reference/비교 곡선 전용, 주황 점선) — 원본처럼 빨강과
    겹치지 않게 분리
  - `color.editable_cell` (옅은 노랑, 원본과 동일하게 유지 — 이미 직관적)
  - `color.primary_curve` (파랑, 유지)
- **PatternFinder drag&drop UI**를 `plan4_rev.md` M24에서 서비스 레이어까지는 만들었으므로,
  이 단계에서 실제 GUI 위젯(drag 소스/drop 타겟, 실시간 필터링)을 구현한다.

#### Acceptance Criteria

- 물질/파라미터 편집이 모달 없이 Inspector dock에서 완료된다.
- 모든 그리드가 `EditableTableWidget` 하나의 구현을 공유한다(중복 코드 없음).
- reference curve와 error 강조색이 시각적으로 구분된다(색상 토큰 유닛 테스트로 hex 값
  비교).

#### Tests

- GUI offscreen 모달 깊이 계측 테스트
- 색상 토큰 회귀 테스트
- PatternFinder drag&drop 상호작용 테스트

---

### M34. Reactor Expansion: PFR, Cascade, Heat Balance

#### Scope

`plan3.md` M16을 실제로 구현한다. `plan_qt6.md`/`plan.md`에서 이미 설계된
`reactor/pfr.py`, `reactor/cascade.py`, `reactor/energy_balance.py` 스켈레톤을 완성한다.

#### Requirements

- **PFR**: plug-flow 근사, 축 방향을 유사-시간축으로 변환해 기존 시간적분기를 재사용
  (`plan.md` 4절의 outer loop 설계를 축 방향 적분에도 적용).
- **Cascade**: N개의 CSTR을 직렬 연결, 각 reactor의 출구가 다음 reactor의 feed가 되는
  구조. `Predici_Maxwell.pdf`에서 확인된 "Multi-Steps: 여러 site/reactor에서 공통 스텝
  재사용" 개념을 반영해 반응 스킴을 reactor 간 공유할 수 있게 한다.
- **Heat balance / heat exchanger**: 반응열(`-DHr`, 각 반응 스텝의 Enthalpy 필드에서
  가져옴, `plan4_rev.md` §1.6에서 이미 스키마에 존재)과 열교환기 UA 값을 이용한 에너지
  수지 ODE를 reactor 온도 방정식에 결합한다. `Temperature: as in reactor` 옵션(Arrhenius
  기준온도)과 정합성을 유지한다.
- **GPC-aware error weighting과의 연동**: PFR/cascade에서도 M26/M34의 core weighting
  계약이 동일하게 작동해야 한다(백엔드 재사용 확인 테스트).

#### Acceptance Criteria

- Cascade의 reactor 수를 늘릴수록 PFR 근사에 수렴함을 수치적으로 확인한다.
- 비등온 batch에서 반응열 부호에 따라 온도가 상승/하강하는 정성적 거동이 맞는다.
- 기존 batch/semi-batch/CSTR 회귀 테스트가 깨지지 않는다.

#### Tests

- `tests/test_pfr.py`, `tests/test_cascade.py`, `tests/test_heat_balance.py`
- cascade→PFR 수렴 벤치마크 (`validation/benchmarks/cascade_to_pfr.py`)

---

### M35. Parameter Estimation v1

#### Scope

`plan3.md` M17을 구현한다. `Predici11_Overview.pdf`에서 확인된 Gauss-Newton(로컬)과
simulated annealing(전역) 두 트랙을 모두 지원한다.

#### Requirements

- `fitting/experiment.py`: 실험 데이터(시간-농도, MWD/GPC 곡선, 모멘트)를 모델 출력과
  매핑하는 `ExperimentMapping` 스키마.
- `fitting/local_search.py`: `scipy.optimize.least_squares`(Levenberg-Marquardt/
  Gauss-Newton 계열) 기반, 자코비안은 유한차분 기본 + 해석적 자코비안 가능하면 우선.
- `fitting/global_search.py`: `scipy.optimize.dual_annealing` 기반.
- 파라미터 estimation 대상 플래그는 `plan4_rev.md` M23에서 추가한
  `Parameter.used_in_optimization`을 그대로 사용한다(중복 스키마 금지).
- 결과: 잔차, 표준오차 근사(자코비안 기반 공분산), 상관행렬.
- GUI: Fitting 탭(기존 `plan_qt6.md` §4.6 설계를 실제 구현)에 실험 데이터 임포트,
  파라미터 테이블(고정/범위), 수렴 곡선 실시간 표시.

#### Acceptance Criteria

- synthetic 데이터(알려진 파라미터로 생성 후 노이즈 추가)에서 원래 파라미터를 지정
  오차 이내로 복원한다.
- 여러 실험(batch 2개 이상)을 동시에 fitting할 수 있다.

#### Tests

- `tests/test_fitting_local.py`, `tests/test_fitting_global.py`
- synthetic recovery 벤치마크 (`validation/benchmarks/synthetic_frp_fit.py`)

---

### M36. Sensitivity Analysis & Shooting Control

#### Scope

`plan3.md` M18~M19를 구현한다.

#### Requirements

- **Sigma-point 민감도**: `Predici11_Overview.pdf`에서 확인된 σ-point 방법(6개 파라미터를
  13번 평가로 처리하는 방식)을 구현한다.
- **Monte Carlo 민감도**: 파라미터를 정규분포로 섭동해 반복 실행, 출력 분산을 집계한다.
- **Shooting control**: 목표(예: 특정 시각의 전환율, 최종 Mw)를 지정하고, 하나 이상의
  조작변수(예: 온도 프로파일, 반응 시간)를 튜닝해 목표에 도달하도록 반복 적분하는
  `engine/shooting.py`. `Predici_Maxwell.pdf`의 "integrated iteration and parameter
  tuning" 개념을 재현한다.

#### Acceptance Criteria

- σ-point 민감도가 브루트포스 유한차분 민감도와 지정 오차 이내로 일치한다.
- shooting control이 단순 목표(예: 목표 전환율 90%에서 반응 종료)에 수렴한다.

#### Tests

- `tests/test_sensitivity.py`, `tests/test_shooting.py`

---

### M37. Copolymer 2D Distribution

#### Scope

`plan.md` 2절이 "가장 어려운 부분, 후순위"로 미뤄둔 2차원 분포(사슬길이 x 조성)를
구현한다. `plan4_rev.md` M23~M24에서 이미 반영된 `is_monomer`, `Copolymerization`
탭, Copolymerization assistant 스키마를 실제 수치 엔진과 연결하는 단계다.

#### Requirements

- `core/basis_2d.py`: 사슬길이 방향은 기존 h-p Galerkin 기저를, 조성 방향은 별도
  저차 다항식(또는 discrete bin) 기저를 사용하는 tensor-product 근사.
- `kinetics/copolymer_terms.py`: terminal model 기준 공중합 반응 텀(교차 성장,
  단일체 소비 경쟁)을 Galerkin 연산자로 변환.
- Balance variables 옵션(`No`/`Per monomer`/`Diades`, `plan4_rev.md` §1.14에서 확인)을
  실제로 지원해, 사용자가 조성 추적 정밀도를 선택할 수 있게 한다.
- 초기 구현 범위는 **2-단량체 terminal model**로 제한하고, r-value 기반 반응계수 입력도
  지원한다(Copolymerization assistant의 `r-values`/`Constants` 옵션과 일치).

#### Acceptance Criteria

- 단일 단량체로 설정하면 기존 동종중합 결과와 수치적으로 일치한다(회귀 방지).
- 공중합 조성 드리프트(예: Mayo-Lewis 방정식 기반 순간 조성)와 비교해 정성적으로 일치한다.
- 계산 비용이 1D 대비 과도하게 폭증하지 않는지(격자 크기 대비 시간) 프로파일링한다.

#### Tests

- `tests/test_copolymer_2d.py`
- Mayo-Lewis 비교 벤치마크 (`validation/benchmarks/copolymer_composition_drift.py`)

---

### M38. Automation API & Export 완결

#### Scope

`plan3.md` 12절에서 스텁으로 남겨둔 automation API를 실제로 구현한다.

#### Requirements

- `api/automation.py`의 각 함수(`create_recipe`, `set_enthalpy`, `get_dist_points`,
  `get_dist_moments`, `activate_detailed_iteration`, `set_heat_exchanger`,
  `check_enthalpy` 등)를 실제 project/engine 객체에 연결한다.
- Export 확장: NPZ(결과 배열), 선택적 moment-equation Matlab/C 코드 생성(원본의
  "script export of core model equations to Matlab or C"에 대응, 후순위 스텁 가능).
- `plan4_rev.md` M26에서 구현한 3-way reference 데이터 경로(`.dat`/구조화 dump/GPC
  import)를 automation API에서도 호출 가능하게 노출한다.

#### Acceptance Criteria

- automation API만으로 튜토리얼 project 하나를 처음부터 끝까지(모델 생성→recipe→실행→
  결과 조회) 재현하는 스크립트가 동작한다.

#### Tests

- `tests/test_automation_api.py`
- `examples/automation_full_workflow.py`

---

### M39. Packaging & Release

#### Scope

`plan3.md` M21/14절을 실행한다.

#### Requirements

- PyInstaller spec 작성, Windows 빌드.
- `dist/PrediciClone/` 산출물 구조(§`plan3.md` 14.2) 유지.
- clean venv에서 빌드 → exe 실행 → sample project open → simulation run → benchmark
  load → CSV/PNG export 스모크 체크리스트 자동화.

#### Acceptance Criteria

- clean Windows VM/컨테이너에서 exe가 추가 설치 없이 실행된다.
- 패키징된 앱에서 튜토리얼 project(M22) 실행이 소스 실행과 동일한 결과를 낸다.

#### Tests

- `scripts/packaging_smoke_test.ps1`

---

### M40. v1.0 Regression Freeze

#### Scope

M8~M39 전체를 아우르는 최종 통합 검증과 문서 동결.

#### Requirements

- 전체 벤치마크(`validation/benchmark_runner.py`)를 fast/medium/slow 등급별로 실행하고
  결과를 `docs/v1_benchmark_report.md`에 기록.
- 매뉴얼(`manual/`) 전체 빌드 및 튜토리얼 매뉴얼 페이지(M31) 최종 검수.
- `CHANGELOG.md` 작성, 버전 태그 `v1.0.0`.

#### Acceptance Criteria

- `pytest -q` 전체(코어/리액터/GUI/피팅/카피올리머/오토메이션) 통과.
- `sphinx-build -W` 경고 없이 통과.
- 패키징된 빌드가 M39 스모크 체크리스트를 통과.

#### Tests

- 전체 회귀 스위트 CI 실행 로그를 `docs/v1_ci_report.md`에 첨부.

---

## 4. Implementation Order

1. M34 reactor 확장 (M35~M36 fitting이 다양한 reactor에서 검증되어야 하므로 먼저)
2. M35 parameter estimation v1
3. M36 sensitivity/shooting
4. M33 GUI modernization (이 시점까지 쌓인 신규 탭들을 한 번에 리팩터링하는 것이 효율적)
5. M37 copolymer 2D distribution (가장 리스크가 크므로 다른 기능이 안정된 후 착수)
6. M38 automation API 완결
7. M39 packaging
8. M40 regression freeze

---

## 5. Risks

### Risk: 2D copolymer 확장이 1D 코드베이스를 광범위하게 건드린다

Mitigation: `core/basis_2d.py`를 1D `core/basis.py`의 상위 호환 확장으로 설계하고,
단일 단량체 경로가 항상 1D와 동치임을 회귀 테스트로 고정한다.

### Risk: GUI 모더나이제이션(M33)이 이미 완성된 M22~M32 화면을 깨뜨린다

Mitigation: 리팩터링 전 각 화면의 offscreen 스모크 테스트를 스냅샷으로 고정하고,
컴포넌트 교체 후 동일 테스트가 통과하는지 확인한다(행동 동등성 우선, 픽셀 동등성은
요구하지 않음).

### Risk: shooting control이 수렴하지 않는 케이스가 많다

Mitigation: 1차 구현은 단순 목표(스칼라 하나, 조작변수 하나)로 제한하고, 다변수 shooting은
v1.0 이후로 미룬다.

### Risk: PyInstaller 패키징에서 SciPy/PySide6 DLL 누락

Mitigation: `plan3.md` 18.5의 대응(먼저 source 실행 안정화, DLL 포함 테스트)을 그대로
따르고, 실패 시 Nuitka로 전환 검토.

---

## 6. Plan5 Completion Criteria

Plan5는 다음이 모두 충족되면 완료된다.

1. PFR/cascade/heat balance가 구현되고 cascade→PFR 수렴이 검증된다 (M34).
2. Gauss-Newton 로컬 탐색과 simulated annealing 전역 탐색이 synthetic recovery
   벤치마크를 통과한다 (M35).
3. σ-point/Monte Carlo 민감도와 shooting control이 동작한다 (M36).
4. GUI가 0절에서 관찰한 시각 패턴을 반영해 모달 깊이 2단 이하로 리팩터링되어 있다 (M33).
5. 2-단량체 terminal-model 공중합 2D 분포가 단일 단량체 회귀와 Mayo-Lewis 비교를
   모두 통과한다 (M37).
6. automation API로 전체 워크플로(모델→recipe→실행→조회)가 재현 가능하다 (M38).
7. Windows PyInstaller 빌드가 clean 환경에서 스모크 체크리스트를 통과한다 (M39).
8. 전체 회귀 스위트와 매뉴얼 빌드가 통과하고 `v1.0.0` 태그가 생성된다 (M40).