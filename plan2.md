# PREDICI 재구현 상세 계획 v2: PyQt6/PySide6 데스크톱 애플리케이션

> 원본 `plan.md`(수치해석 코어 중심 계획)를 유지하면서, **Qt 기반 GUI 애플리케이션으로서의
> 아키텍처, 화면 설계, 스레딩/데이터 흐름, 패키징**을 추가한 확장판입니다.
> Predici11_Overview.pdf / Predici_Maxwell.pdf에서 확인되는 실제 PREDICI UI 구성 요소를
> 참고해 기능 매핑을 했고, 관련 최신 문헌도 반영했습니다.

---

## 0. Qt 버전 선택: PyQt6 vs PySide6

라이선스 문제 때문에 상용/배포 목적이라면 **PySide6(LGPL, Qt Company 공식)**를 기본으로
권장합니다. `PyQt6`는 GPL/상용 이중 라이선스라 배포 시 제약이 생길 수 있습니다.
API는 거의 동일(시그널 연결 문법만 `pyqtSignal` vs `Signal` 등 차이)하므로, 아래 계획은
`PySide6` 기준으로 작성하되 필요하면 `PyQt6`로 거의 그대로 포팅 가능합니다.

```
pip install PySide6 pyqtgraph numpy scipy numba pydantic PyYAML qtawesome
```

---

## 1. 전체 아키텍처: Core / GUI 완전 분리

가장 중요한 설계 원칙은 **"수치 코어는 Qt를 전혀 모른다"**입니다. `core/`, `kinetics/`,
`integrator/`, `reactor/` 는 순수 Python(NumPy/SciPy)로만 작성하고, Qt 관련 코드는
`gui/` 아래에만 존재합니다. 이렇게 해야:

- 코어를 CLI/노트북/배치 스크립트에서도 그대로 재사용 가능
- 코어 로직을 pytest로 GUI 없이 단위 테스트 가능
- 나중에 GUI를 웹(Qt for WebAssembly, 또는 별도 웹앱)으로 교체해도 코어 재사용 가능

```
predici-clone/
├── core/                    # (기존 계획과 동일, Qt 비의존)
├── kinetics/
├── integrator/
├── reactor/
├── postprocess/
├── api/
│   ├── scheme_loader.py     # YAML/JSON ↔ 내부 모델 객체
│   └── project_schema.py    # pydantic 모델: Substance, Polymer, ReactionStep, Recipe, Reactor...
├── engine/
│   └── simulation_engine.py # GUI가 호출하는 단일 진입점. QObject 아님, 순수 파이썬.
├── gui/
│   ├── app.py                # QApplication 진입점
│   ├── main_window.py        # QMainWindow, 도킹 레이아웃 조립
│   ├── models/                # Qt 모델(QAbstractItemModel) - project_schema를 트리로 노출
│   │   ├── project_tree_model.py
│   │   └── reaction_table_model.py
│   ├── views/
│   │   ├── model_builder/     # 반응기/물질/폴리머/반응스텝 편집 화면
│   │   ├── recipe_editor/     # 초기조건/공급 스트림 편집
│   │   ├── simulation_panel/  # Run/Stop/진행률/로그
│   │   ├── plot_dock/         # pyqtgraph 기반 실시간 차트
│   │   ├── mwd_viewer/        # 분포(로그스케일) 뷰어
│   │   └── fitting_panel/     # 파라미터 추정 UI
│   ├── workers/
│   │   └── simulation_worker.py  # QThread/QObject 워커, engine을 감쌈
│   ├── dialogs/
│   │   ├── reaction_step_dialog.py
│   │   └── substance_dialog.py
│   └── resources/             # 아이콘, .qss 스타일시트
├── validation/
└── tests/
    ├── test_core/             # Qt 없이 순수 코어 테스트
    └── test_gui/              # pytest-qt로 위젯/워커 테스트
```

`engine/simulation_engine.py`가 핵심 경계입니다. GUI는 이 클래스의 메서드만 호출하고,
콜백(진행률, 스텝 완료, 그리드 적응 이벤트)은 순수 파이썬 콜백(함수)으로 등록합니다.
Qt 시그널로의 변환은 `simulation_worker.py`에서만 일어납니다.

```python
# engine/simulation_engine.py (Qt 비의존)
class SimulationEngine:
    def __init__(self, project: ProjectModel): ...
    def run(self, t_span, on_step=None, on_grid_adapt=None, should_stop=None):
        """on_step(t, moments, coeffs), on_grid_adapt(interval_info) 콜백.
        should_stop() -> bool 로 취소 지원."""
```

---

## 2. 스레딩 모델 (Qt 필수 사항)

시뮬레이션은 수 초~수 분 걸릴 수 있는 stiff ODE/DAE 적분이므로, **절대 메인(GUI) 스레드에서
직접 돌리면 안 됩니다.** `QThread` + worker `QObject` 패턴(moveToThread 방식)을 사용합니다.

```python
class SimulationWorker(QObject):
    progress = Signal(float)                 # 0~1
    step_done = Signal(float, dict)           # t, moments dict
    grid_adapted = Signal(dict)               # h/p 적응 이벤트 정보
    finished = Signal(object)                 # 최종 결과 객체
    error = Signal(str)

    def __init__(self, engine: SimulationEngine, t_span):
        super().__init__()
        self._engine = engine
        self._t_span = t_span
        self._stop_requested = False

    @Slot()
    def run(self):
        try:
            result = self._engine.run(
                self._t_span,
                on_step=lambda t, m: self.step_done.emit(t, m),
                on_grid_adapt=lambda info: self.grid_adapted.emit(info),
                should_stop=lambda: self._stop_requested,
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    @Slot()
    def request_stop(self):
        self._stop_requested = True
```

```python
# main_window.py 쪽
self.thread = QThread()
self.worker = SimulationWorker(engine, t_span)
self.worker.moveToThread(self.thread)
self.thread.started.connect(self.worker.run)
self.worker.step_done.connect(self.plot_dock.append_point)   # 자동 큐잉, 스레드-세이프
self.worker.finished.connect(self.on_simulation_finished)
self.worker.finished.connect(self.thread.quit)
self.thread.start()
```

**주의점**

- 실시간 플롯 업데이트를 `step_done`마다 매번 다시 그리면 GUI가 느려집니다. `QTimer`로
  50~100ms 배치 업데이트(최근 콜백 결과를 버퍼링 후 한번에 그리기)를 권장합니다.
  (PREDICI도 "online data" 갱신을 그래픽 창 뒤에서 배치로 처리합니다 — Predici11_Overview.pdf)
- 가변 크기 상태벡터(h-p 적응)로 인해 `step_done` payload 구조가 스텝마다 바뀔 수 있으므로,
  GUI 쪽은 payload를 dict로 받아 방어적으로 파싱해야 합니다.
- 취소(`request_stop`)는 반드시 적분기 루프 내부에서 폴링 가능한 지점에 넣어야 하며,
  Qt 시그널로 직접 스레드를 kill하면 안 됩니다.

---

## 3. 플로팅: pyqtgraph 권장 (Matplotlib 대신)

- **실시간 갱신 + 대용량 데이터(적응 그리드로 인해 곡선 포인트 수가 자주 바뀜)** 요구사항에는
  `pyqtgraph`가 Matplotlib보다 훨씬 빠릅니다 (OpenGL 가속, 증분 업데이트).
- MWD/GPC 곡선은 로그 스케일(x: log(n) 또는 log(M)) 표시가 표준이므로
  `PlotWidget.setLogMode(x=True)` 활용.
- 모멘트 시계열(Mn, Mw, PDI)은 별도 도킹 위젯으로, 다중 y축(예: 온도 vs 전환율) 지원.
- Matplotlib은 "내보내기용 정적 이미지/논문용 플롯" 생성 시 보조로만 사용 (File > Export
  기능에서 고품질 PNG/PDF/SVG로 재렌더링).

---

## 4. 화면 설계 (PREDICI 11 UI 매핑)

프로젝트에 첨부된 `Predici11_Overview.pdf`를 보면 PREDICI UI는 다음 흐름으로 모델을
구축합니다: <cite>화학 모델을 손쉽게 구축하고, 레시피/초기조건을 입력하고, 결과를 즉시
시각화하며, 사슬 구조를 세밀하게 탐색할 수 있는 인터페이스</cite>를 제공합니다.
또한 모델 커스터마이징은 <cite>반응기 설정 → 물질 입력 → 폴리머 구성 → 반응 파라미터
입력 → 반응 스텝 커스터마이징</cite> 순서로 이루어집니다. 이를 Qt 도킹 위젯 구조로 아래처럼
매핑합니다.

### 4.1 메인 윈도우 레이아웃

```
┌─────────────────────────────────────────────────────────────────┐
│ MenuBar: File Edit Model Recipe Simulate Analysis Fitting Help    │
├───────────────┬─────────────────────────────────┬─────────────────┤
│ Project Tree   │      중앙 탭 영역                  │  Inspector       │
│ (Dock, 좌측)   │  [Model Builder] [Recipe]        │  (Dock, 우측)    │
│                │  [Simulation]    [MWD Viewer]     │  선택 항목 속성  │
│ - Reactor      │  [Fitting]        [Script]        │  편집 폼        │
│ - Substances   │                                    │                 │
│ - Polymers     │                                    │                 │
│ - Reactions    │                                    │                 │
│   - Initiation │                                    │                 │
│   - Propagation│                                    │                 │
│   - Termination│                                    │                 │
│ - Recipes      │                                    │                 │
│ - Results      │                                    │                 │
├───────────────┴─────────────────────────────────┴─────────────────┤
│ Bottom Dock: Log / Progress bar / Run-Stop-Pause 버튼               │
└─────────────────────────────────────────────────────────────────┘
```

`QMainWindow.addDockWidget` + `QTabWidget`(중앙)으로 구성. 프로젝트 트리는
`QTreeView` + `ProjectTreeModel(QAbstractItemModel)`으로, `project_schema.py`의
pydantic 객체를 감싸는 어댑터입니다.

### 4.2 Model Builder 탭

- 좌측: 반응 스텝 팔레트(드래그 가능한 아이콘 리스트) — Initiation, Propagation,
  ChainTransferToMonomer, ChainTransferToAgent, TerminationCombination,
  TerminationDisproportionation, Branching, Scission, Copolymerization 등
- 중앙: 캔버스 또는 표(QTableView) 형태로 현재 반응 스킴 나열, 더블클릭 시
  `ReactionStepDialog` 오픈
- `ReactionStepDialog`는 반응식(예: `R• + M -> P1`), 속도상수(Arrhenius A, Ea 또는
  상수), 관련 물질 선택 콤보박스를 포함. "저장" 시 `kinetics/reaction.py`의 DSL 객체로
  직렬화되어 `assemble(basis, grid)` 호출 가능해야 함(코어 계획의 요구사항과 정합).

### 4.3 Recipe 탭

PREDICI는 <cite>중합체 종, 입자, 또는 프로파일(GPC/PSD 데이터 등)로 입력을 구성할 수
있고, 온도·압력 제어를 조정할 수 있으며, 다양한 입력 유형 간 직접 변환을 지원하고,
개별 조성·설정을 가진 여러 개의 공급 탱크를 열 수 있는</cite> 레시피 편집 기능을 제공합니다.
이를 Qt로는:

- `QTableWidget` 기반 초기 농도 입력 (물질별 행)
- `QTabWidget` 내부에 "Feed Tank #1, #2, ..." 추가/삭제 가능한 동적 탭
- 온도/압력 프로파일: 상수 값 또는 시간에 따른 프로파일(테이블 또는 수식) 토글

### 4.4 Simulation 탭

- 상단: 적분기 설정 (BDF/Radau, rtol/atol, 초기 h-p 그리드 설정)
- 실행 버튼 → `simulation_worker` 스레드 기동
- 진행률 바 + 로그(QPlainTextEdit, 스텝 실패/그리드 재조정 이벤트 append)
- 실시간 pyqtgraph: 전환율(conversion), Mn/Mw/PDI 시계열

### 4.5 MWD Viewer 탭

- 로그 스케일 분포 곡선 (`pyqtgraph`, x=log10(사슬길이) 또는 log10(M))
- 시간 슬라이더로 시각(t) 스캔하며 분포 애니메이션
- 여러 케이스(파라미터 스윕) 오버레이 비교 기능

### 4.6 Fitting 탭 (파라미터 추정)

PREDICI 문서에 따르면 파라미터 추정은 <cite>국소 탐색(Gauss-Newton, 뉴턴법의 확장이며
0이 아니라 최솟값을 찾기 위한 방법)과 전역 탐색(box, simulated annealing)</cite>을
제공하며, 민감도 분석은 <cite>σ-point 방법으로 소수의 평가만으로 파라미터 변동에 대한
민감도를 계산</cite>합니다. Qt 구현:

- 파라미터 테이블(초기값/하한/상한/고정 여부 체크박스)
- 실험 데이터 임포트(CSV/GPC 파일) → `QTableView`로 표시, 플롯에 마커 오버레이
- `scipy.optimize.least_squares`(Gauss-Newton/Levenberg-Marquardt 지원) 또는
  전역 탐색은 `scipy.optimize.dual_annealing` 활용, 별도 워커 스레드에서 실행하며
  반복마다 residual을 시그널로 GUI에 전달해 수렴 곡선을 실시간 표시
- 결과: 잔차, 신뢰구간(자코비안 기반 근사), 상관행렬 히트맵(pyqtgraph `ImageItem`)

### 4.7 Script 탭 (선택 기능)

PREDICI는 <cite>열수지, 컨트롤러, 물질 물성 등에 사용할 수 있는 간단한 스크립트
언어로 시스템 변수를 고수준 명령으로 접근</cite>할 수 있게 합니다. Python 재구현에서는
이 기능을 **내장 Python 콘솔(QsciScintilla 또는 `qtconsole`/IPython 위젯)**로 대체하면
자연스럽습니다 — 사용자가 직접 Python으로 커스텀 출력/반응속도식을 정의하도록.
보안상 `exec()` 샌드박싱(허용 네임스페이스 제한)이 필요합니다.

---

## 5. 프로젝트 파일 포맷 & 스키마

- `.predici-clone` 프로젝트 파일은 YAML 또는 JSON, `pydantic` 모델로 스키마 검증
- 저장 시 (a) 모델 정의(물질/반응/반응기), (b) 레시피(초기조건/공급), (c) 마지막 시뮬레이션
  설정, (d) 결과 캐시(선택, 큰 경우 별도 `.h5` 파일로 분리 — `h5py` 사용 권장, 시계열+분포
  계수 배열이 커질 수 있으므로)를 분리 저장
- `api/scheme_loader.py`가 YAML ↔ pydantic ↔ 코어 객체(`kinetics.Reaction` 등) 변환 담당
- Undo/Redo: `QUndoStack` + `QUndoCommand`로 모델 편집(반응 추가/삭제/파라미터 변경)을
  커맨드화 — PREDICI의 "model comparison/alternative models" 기능(<cite>대안 모델과
  파라미터, 반응 그룹, 모델 비교 등을 포함하는 정교한 "all-in-one" 모델/프로젝트
  관리</cite>)을 재현하려면 필수

---

## 6. 최신/관련 수치해석 문헌 (원본 계획 보강)

원본 `plan.md`가 인용한 Wulkow(1996) 외에, 실제 구현 시 참고할 후속 연구들을 검색했습니다.

1. **Wulkow (1996)**, *"The simulation of molecular weight distributions in polyreaction
   kinetics by discrete Galerkin methods"*, Macromol. Theory Simul. — <cite index="12-1">discrete
   Galerkin h-p 방법에 기반한 종합 솔버(PREDICI)의 개발을 설명하며, 다양한 중합 반응 유형을
   효율적으로 처리할 수 있다</cite>는 원 논문. (원본 계획에 이미 반영됨)

2. **Deuflhard, Huisinga, Jahnke, Wulkow (2007)**, *"Adaptive Discrete Galerkin Methods
   Applied to the Chemical Master Equation"*, SIAM J. Sci. Comput. — discrete Galerkin
   h-p 방법을 화학 마스터방정식(확률적 반응 시스템)으로 확장한 후속 연구. h-p 오차 추정자
   설계의 이론적 근거를 더 최신 버전으로 참고하기 좋습니다. `core/error_estimator.py` 설계 시
   원 논문(1996)보다 이 논문의 오차 추정 프레임워크가 더 정교합니다.

3. **PARSIVAL (결정화 공정 적용 논문)**, *"Modeling and simulation of crystallization
   processes using parsival"*, Chem. Eng. Sci. — <cite index="11-1">분자량분포 시뮬레이션을 위한
   discrete Galerkin h-p 방법(Wulkow, 1996)의 개발이 본 연구의 출발점이었으며, 중합과
   결정화 모델 사이의 구조적 유사성이 커서 PREDICI에 구현된 성공적인 알고리즘을 연속
   property 좌표로 변환할 수 있었다</cite>고 밝히고 있고, <cite index="11-1">이 새로운 접근법은
   시간 이산화와 property 좌표 이산화 모두에 대해 자동 오차 제어를 갖춘 완전 적응형
   Galerkin h-p 방법을 결과로 낸다</cite>고 설명합니다. **discrete-continuous 경계 처리**
   (원본 계획 8절의 가장 큰 리스크) 설계 시 이 논문이 참고할 만한 "연속 좌표로 일반화한
   버전"을 제공하므로 매우 유용합니다.

4. **State-of-the-art 리뷰 (2020년대)**, *"Numerical Techniques for the Solution of the
   Molecular Weight Distribution in Polymerization Mechanisms"* — <cite index="13-1">discrete
   Galerkin h-p 방법(특히 Wulkow의 접근법)은 다양한 중합 화학에 대해 강건한 해를 제공하지만
   구현 복잡도가 높다</cite>고 평가하며, Monte Carlo/모멘트법과의 비교표를 제공합니다.
   재구현 우선순위(M1~M7) 판단에 참고할 만합니다.

5. **Computation of MWD for MMA (Wulkow 초기 응용 논문)** — <cite index="17-1">discrete Galerkin
   방법을 실제 메틸메타크릴레이트(MMA) 중합 예제에 적용했고, 이산 변수의 직교다항식 기반
   Galerkin 근사를 사용하며, 시간/모멘트에 의존하는 반응계수를 가진 완전한 반응 스킴의
   해를 소수의 미분방정식으로 축소해 효율적으로 계산할 수 있다</cite>고 보고하며,
   <cite index="17-1">MMA 준정상상태 근사 기준 표준 방법 대비 약 25배의 계산량 절감</cite>을
   보였습니다 — M4 벤치마크(로드맵 4절)의 목표 성능 지표로 삼기 좋습니다.

**참고**: 이산 Galerkin/h-p 계열 외에 경쟁 방법론(고정-피벗 이산화, wavelet-Galerkin,
OCFE)도 검색됐지만, 이들은 대개 PREDICI 접근법과 다른 계열이며 "finite element/Galerkin
계열은 복잡한 구현과 낮은 계산 효율성 때문에 덜 매력적"이라는 비판도 존재합니다
(<cite index="2-1">유한요소법, 특히 직교 콜로케이션과 Galerkin 기법은 수치적 문제를 심각하게
겪을 수 있고, 복잡한 구현과 낮은 계산 효율성 때문에 이러한 방법들은 해당 응용에 덜
매력적</cite>). 이 비판은 **일반적인 정적 Galerkin FEM**에 대한 것이고, Wulkow의
**h-p 적응 + discrete-continuous 처리**가 그 한계를 극복하기 위한 핵심 혁신이라는 점을
재구현 시 항상 염두에 둬야 합니다 — 즉, "단순 Galerkin FEM"이 아니라 "적응적 h-p +
경계 처리"까지 구현해야 실사용 가능한 성능이 나옵니다.

---

## 7. 개정된 로드맵: 코어 트랙 + GUI 트랙 병행

원본 로드맵(M0~M7)은 유지하되, GUI 개발을 별도 트랙으로 병행합니다. GUI 트랙은 코어가
어느 정도 안정화된 후 "얇은 스크립트/노트북 인터페이스"부터 시작해 점진적으로
Qt 앱으로 확장하는 것을 권장합니다 (초기부터 풀 GUI를 만들면 코어 API가 계속
바뀌어 GUI도 계속 다시 짜야 함).

| 단계 | 코어 트랙 | GUI 트랙 |
|---|---|---|
| M0 | 설계 문서, 아키텍처 확정 | Qt 프로젝트 스캐폴딩, `project_schema.py` 초안 |
| M1 | 단일구간 Galerkin + 순수 성장 | 없음 (matplotlib 스크립트로 충분) |
| M2 | 정지/이동 + h-refinement | `SimulationEngine` 1차 API 확정 (콜백 인터페이스) |
| M3 | p-refinement + discrete-continuous | `SimulationWorker`(QThread) + 최소 MainWindow, 실시간 모멘트 플롯만 |
| M4 | 저분자종 커플링 + FRP 전체 스킴 batch | Model Builder 탭 (반응 스킴 편집 UI), MWD Viewer 탭 |
| M5 | Semi-batch/CSTR | Recipe 탭(공급 탱크), Reactor 설정 UI |
| M6 | 후처리/모멘트 리포트 | Fitting 탭, 결과 내보내기(Excel/CSV/PNG), 프로젝트 저장/불러오기 + Undo/Redo |
| M7 | (옵션) 공중합/2D 분포, GUI 고도화 | 다크테마(`qdarktheme`), 아이콘(`qtawesome`), Script 콘솔, 패키징 |

---

## 8. 테스트 전략 (GUI 포함)

- 코어: `pytest` + 해석해(Flory-Schulz) 대비 오차 검증 (기존 계획 유지)
- GUI: `pytest-qt`(`qtbot`)로 위젯 상호작용 테스트 — 예: "Run 버튼 클릭 → 워커 스레드 시작
  → finished 시그널 수신 시 결과 dock 갱신" 시나리오를 실제 Qt 이벤트 루프에서 검증
- 워커/시그널 로직은 `SimulationEngine`을 mock으로 대체해 GUI 로직만 독립적으로 테스트
- 회귀 테스트: 저장된 `.predici-clone` 프로젝트 파일들을 validation/ 폴더에 축적해
  "불러오기 → 재실행 → 이전 결과와 비교" CI 파이프라인 구성

---

## 9. 패키징 & 배포

- 개발 중: `uv` 또는 `poetry`로 의존성 관리
- 배포: `PyInstaller`(가장 무난) 또는 `Nuitka`(더 빠른 실행파일, 빌드 복잡도 ↑)
- Numba JIT 사용 시 PyInstaller 빌드에서 컴파일 캐시 이슈 주의 (첫 실행 지연 발생 가능,
  `NUMBA_CACHE_DIR`를 앱 데이터 폴더로 고정 권장)
- 크로스플랫폼: Windows/macOS/Linux 모두 지원하려면 CI에서 3개 OS 매트릭스 빌드 필요
  (GitHub Actions 무료 러너로 가능)
- 아이콘/브랜딩: `.qss` 스타일시트로 PREDICI풍 또는 독자적인 다크/라이트 테마 구성

---

## 10. 리스크 (Qt 특화 추가분)

- **스레드 안전성**: 코어 객체(그리드, 계수 배열)를 워커 스레드에서 수정하는 동안 GUI
  스레드가 동시에 읽으면 안 됨 — 반드시 시그널/슬롯의 큐 연결(자동 큐잉)을 통해서만
  데이터를 GUI로 전달하고, 코어 객체에 대한 직접 참조를 GUI 위젯에 넘기지 않는다.
- **가변 크기 상태(h-p 적응) → UI 모델 동기화**: 그리드가 적응할 때마다 `ProjectTreeModel`/
  플롯의 데이터 구조가 바뀌므로, `beginResetModel/endResetModel` 또는 세밀한
  `dataChanged` 시그널 관리가 필요 (전체 리셋 남발 시 UI가 깜빡이거나 느려짐).
- **대용량 결과 데이터**: 긴 batch 시뮬레이션의 전체 시간 이력(분포 계수 스냅샷)을
  메모리에 다 들고 있으면 GUI가 느려질 수 있음 — 다운샘플링해서 플롯하고, 원본은
  디스크(HDF5)에 스트리밍 저장 후 필요 시 lazy load.
- **크로스플랫폼 폰트/DPI**: 과학 플롯의 축 라벨(첨자, 그리스 문자 Mn, Mw 등) 렌더링이
  플랫폼별로 다르게 보일 수 있음 — pyqtgraph의 `TextItem`/`AxisItem` 커스터마이징 필요.

---

## 11. 다음 액션 제안

1. `engine/simulation_engine.py`의 콜백 인터페이스를 먼저 확정 (GUI/코어 경계).
2. 코어 M1(단일구간 Galerkin + 순수 성장)을 스크립트로 완성.
3. 그 결과를 소비하는 최소 `MainWindow`(플롯 1개 + Run 버튼만)를 만들어 M3 단계에서
   `SimulationWorker` 패턴을 조기에 검증 — 스레딩 버그는 나중에 찾으면 리팩토링 비용이 크므로
   가능한 한 일찍 파이프라인을 통째로(코어 → 엔진 → 워커 → GUI) 관통시켜 보는 것을 권장합니다.

원하시면 위 구조대로 `gui/main_window.py` + `gui/workers/simulation_worker.py` +
최소 동작하는 더미 엔진(사인파 등 가짜 시뮬레이션)으로 된 **스켈레톤 Qt 앱**부터
바로 만들어 드릴 수 있습니다.
