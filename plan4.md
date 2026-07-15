# PREDICI Clone 개발 계획 v4 (Revised): Tutorial-Driven Modeling Workflow

이 문서는 `plan4.md`를 `Predici11_Tutorials.pdf` (Basic Tutorial: Polyethylene Task 1/Task 2,
PRESTO-KINETICS/Oregonator Tutorial) 원문을 스크린샷 단위까지 재검토하여 개정한 버전이다.
`plan4.md`는 튜토리얼의 **작업 흐름(workflow)** 은 잘 정리했지만, 실제 다이얼로그의
**필드 구성, 입력 방식, 출력/차트 조작 방식**까지는 충분히 세밀하지 않았다. 이번 개정에서는
다음을 보강한다.

1. 각 다이얼로그(Reactor, Substance, Distribution, Parameter, Reaction step, Recipe,
   Graphs, Chart administration, Script/Interpreter, Debug)의 **필드 단위 스펙**을 명시한다.
2. 데이터 **입력 방식**(입력 모드 전환, consistency 계산, 자동 선언, PatternFinder drag&drop)과
   **출력 방식**(chart 구성, GPC 표현, reference overlay, raw data, export)을 구체적으로 반영한다.
3. `plan3.md`까지 이미 구현된 범위(현재 저장소 기준선)를 다시 훼손하지 않는 선에서
   증분 마일스톤(M22~M32)으로 재정리한다.

> 이 문서는 `plan4.md`를 대체하는 개정판이다. `plan4.md`의 목표/철학/비목표는 그대로 유지하되,
> 세부 요구사항이 이 문서 기준으로 갱신된다. 두 문서가 충돌하면 이 문서(`plan4_rev.md`)를
> 따른다.

참조 문서:

- `Predici11_Tutorials.pdf` (Basic Tutorial 1-53p: Polyethylene, PRESTO-KINETICS/Oregonator
  Tutorial 1-18p) — 이번 개정에서 원문 전체를 재검토했다.
- 기존 완료 범위: `plan3.md`, `docs/plan3_completion_audit.md`
- 이전 개정: `plan4.md` (본 문서로 대체)

---

## 0. 개정 사유 요약 (plan4.md 대비 변경점)

| 영역 | plan4.md | 이번 개정에서 보강한 내용 |
| --- | --- | --- |
| Reactor | operation mode 언급만 있음 | batch/semibatch/continuous/tubular reactor 4가지 모드, Phases, Temperature+Pressure, Volume, Copolymerization, Profile properties 탭 구조 명시 |
| Substance/Distribution | 필드 목록이 개략적 | General/Thermodyn. data/Recipe values/Comment 탭 구성, phase setting(Main/Own/Reactive), density 선형식 `rho = a - T*b`, heat capacity 다항식, Distribution 전용 필드(Oligomer, max chain length, Monte Carlo ensemble size) 명시 |
| Parameter | Arrhenius 언급만 있음 | Arrhenius 세부 필드(k0, E/R, 기준온도, 기준 reactor, DV/R, temp basis), `show in outsplitter`, `online-change allowed`, `used in optimization` 플래그 명시 |
| Reaction builder | PatternFinder 존재만 언급 | 필터 탭 구조(All/Standard/Copolymerization/Special1/Flow/Phases/Profiles/Balance/Used in model), drag&drop 팔레트 UI, 자동 선언 확인 다이얼로그(Ja/Nein), 일반 kinetic step의 5x5 (n_i, order_i)/(m_i, order_i) 행렬 구조 명시 |
| Recipe | consistency 개념만 언급 | 7가지 입력 모드 전환 드롭다운, consistency 공식과 red-sum 표시, 두 가지 서로 다른 보정 액션(Set concentration consistent / Set rest) 구분, Tank/Feed 다이얼로그 필드 명시 |
| Chart/Output | "chart administration 부족" 정도로만 서술 | 2-pane Chart administration 다이얼로그(Charts on pages / Graphs in chart), General/Optical/Points 탭, Distribution/Moment/Monte-Carlo graphic mode, GPC 표현식(`W(log M) ∝ P(s)·s^2`) 명시, Components information board 팝업 필드, `.dat`/`mdf-file`/GPC 데이터 로더 구분 |
| Script | 함수 목록이 일부만 있음 | 실제 확인된 함수 카탈로그(`getx, getco, getconsum, getcf, getcoini, addvalue, getuxr, getmy, weightedmy, getkp, getkpreac, setkp, getkpt, getkptp, gettotalmy`), Template 자동생성 기능(species/parameter 체크리스트 + Apply template), Script selection 재사용 패턴 명시 |
| Debugger | 개략적 요구사항만 있음 | 다중 스크립트 탭 debug 창, +/- 스크립트 추가/제거, "move to window", run-to-time 필드, edit-in-place 흐름 명시 |
| Simulation mode | 언급 없음 | Distributions/Moments 전역 토글이 결과 정확도/속도 트레이드오프에 필수임을 반영해 M32 신설 |
| 외부 의존성 | Wingraphviz 언급 없음 | 원문은 외부 프로그램(Wingraphviz)에 의존하는 구조 그래프 기능이 있음 → 이 clone은 외부 바이너리 의존 없이 Python-native(graphviz/networkx) 대체를 제공하는 것으로 비목표를 명확히 함 |

---

## 1. PDF 재검토 상세 (다이얼로그/필드 단위)

### 1.1 Workshop / Project 설정

- 새 프로젝트 생성 리본: `New empty project` / `New project` / `Copolymerisation project`.
- Workshop 최상단 입력: project name/comment, `End time`, `Schedule`, `Arrays`, `Database`
  경로, `Initial data`(File/Value), `Initial chain length`, `Initial data set (*.ids)`,
  `Snapshot file`.
- 시뮬레이션 모드 전역 라디오 버튼: `Distributions` vs `Moments` (+ `incl. Monte Carlo
  method`, `use tau leaping`). Moments 모드는 전체 분포 대신 모멘트 ODE만 풀어 훨씬 빠르지만
  근사이며, Distributions 모드가 기준(reference) 결과로 쓰인다. 튜토리얼은 실제로 두 모드를
  번갈아 실행해 moment 결과를 `.dat`로 저장한 뒤 distribution 결과와 겹쳐 그려 정확도를
  검증한다.
- `Physical units (output)`: Mass/Volume/Time/Energy 단위 드롭다운. 단위는 절대 자동
  변환되지 않으며 입력 편의용 메모일 뿐이라는 점이 명시적으로 강조된다. 즉 project 저장 후
  단위를 바꿔도 저장된 숫자 값은 그대로 유지된다.
- 좌측 내비게이션 트리(고급 모드): `Model components`(Reactors/Substances/Distributions/
  Parameter/Profiles/Modules), `Project extension`(Library/Recipes/Settings/Scripts),
  `Optimization/Variation`, `Estimation`. 이 트리 + `Group filter`(Type 필터, Reactor 필터,
  Group 필터 다중 리스트) 조합으로 대형 모델을 탐색한다.

### 1.2 Reactor 다이얼로그

필드/탭:

- `Name` (필수, 사용자 정의, alias 규칙과 동일하게 blank 불가)
- 탭: `Operation mode + control`, `Phases`, `Temperature + Pressure`, `Volume`,
  `Copolymerization`, `Profile properties`, `Compo...`(compositions) 등 다수
- `Operation mode`: `batch` / `semibatch` / `continuous` / `Tubular reactor`
  - continuous: `Control stream` Type + `Switch off after [s]`
  - Tubular reactor: `Length[m]`, `Diameter[m]`, `Mass flow rate[g/s]`, `Velocity[m/s]`,
    `based on flow velocity` 체크, `Relative velocity`(script 가능)
- `Active` 체크박스 (reactor 자체도 비활성화 가능)

### 1.3 Substance (elemental species) 다이얼로그

- 상단: `Name`, `Alias`, `Group` (드롭다운, 자유 입력으로 새 그룹 생성 가능), `Reactor`
- 탭 `General`:
  - `Molmass [g/mol]`
  - `is Monomer` 체크 (동종중합에서도 향후 공중합 확장을 고려해 체크 권장)
  - `algebraic` 체크
  - `use database value` 체크
  - `Phase setting`: `Main phase` / `Own phase` / `Reactive phase`(활성 phase 선택)
  - `Output`: `Console`, `Overview` 체크박스 (출력 노출 범위 제어)
- 탭 `Thermodyn. data`:
  - `Density [g/l], T[C]`: `linear` 라디오 → `rho = a - T * b` 형태의 두 계수 입력,
    또는 `function` 라디오 → 임의 함수식 `f(T,p,v)=0` (+ `explicit` 체크),
    또는 `use database function` 체크
  - `Heat capacity [kJ/g/K]`: `polynomial` 라디오 → 4개 계수(상수, `*T`, `*T^2`, `*T^3`) +
    `T in Kelvin` 체크, 또는 `function` 라디오 → `f(T,p,X)`
- 탭 `Thermodyn. data copolymer`: 공중합 확장용 열역학 데이터 (동종중합에서는 비워둠)
- 탭 `Recipe values`, `Comment`: 자유 서술
- Copy 기능: `New` 버튼을 눌러 저장과 동시에 다음 입력으로 넘어가는 연속 입력 흐름,
  그리고 별도의 "Copy" 옵션으로 이미 입력한 물질의 분자량 등을 재사용해 유사 물질(예:
  initiator → initiator radical)을 빠르게 생성하는 흐름이 별도로 존재한다.

### 1.4 Distribution (polymer species) 다이얼로그

Substance와 유사하지만 사슬 분포 전용 필드가 추가된다.

- `General` 탭:
  - `Molmass elemental species [g/mol]` (단량체 단위 분자량 - 사슬길이 s에 대응하는 반복단위
    질량)
  - `ignore copolymer balance` 체크
  - `algebraic` 체크, `sMin = 0` 체크(최소 사슬길이 경계 처리 옵션)
  - `Recipe settings`: `Initial concentration [mol/l]`, `Script`, `Grid`, `Feed` - 각각
    파일/스크립트 참조 가능
  - `Options`: `Oligomer` 체크, `maximal chain length` 체크+값, `Molar mass fragment`
  - `Monte Carlo method`: `Ensemble size` (기본 100)
- `Thermodyn. data` 탭: Substance와 동일한 density(linear a - T*b)/heat capacity 구조

### 1.5 Parameter 다이얼로그

- `Name`, `Alias`, `Group`
- `Value` 라디오: 단일 상수값 + 단위(memo)
- `Arrhenius expression` 라디오:
  - `k0` (pre-exponential), `E/R [K]` (활성화 에너지/기체상수)
  - `opt.: Ref. temp.` (기준 온도, Celsius 단위 선택 가능)
  - `Reactor` (기준 reactor 지정 - reactor마다 다른 온도 프로파일을 참조 가능)
  - `DV/R` (활성화 부피 보정)
  - `Temp.`: `as in reactor` 또는 명시적 온도, 단위 `cm^3*K/J` 등
- 플래그: `show in outsplitter`, `online-change allowed`, `used in Priamoz optimization`
  (parameter estimation 대상 여부 플래그로 재해석)
- 숫자 상수도 이름이 있는 Parameter로 등록해야 한다. 예: 화학양론 계수 `2`나 역반응
  계수 `0`도 `"2"`, `"0"`이라는 이름의 Parameter로 자동/수동 등록된다. 이는 프로젝트 내
  모든 사용된 값의 목록을 일관되게 유지하기 위한 설계 원칙이다.
- 리스트 정렬: 사용자 정의 순서(drag&drop, 상하 화살표) 또는 컬럼 클릭 자동 정렬 토글.

### 1.6 Reaction Step Modules - PatternFinder

- 진입점: `Modules` 탭 → `New` → Reaction step modules 카탈로그 다이얼로그.
- 카탈로그 필터: `Filter by string` 텍스트 검색 + 탭
  (`All`/`Standard`/`Copolymerization`/`Special 1`/`Flow`/`Phases`/`Profiles`/`Balance`/
  `Used in model`).
- 리스트 컬럼: `No.`, `Name`, `Pattern`, `Flow`, `Moment's cl.`(closed 여부), `Copolymeriz.`,
  `Profile`, `Balance` - 각 스텝 템플릿이 어떤 성질(모멘트 폐포성, 공중합 지원, PDE profile
  연동, 물질수지 검사)을 갖는지 한눈에 보여준다.
- PatternFinder 그래픽 모드 (`Pattern` 탭): 반응식 구조를 그래픽 아이콘(Educt1 -> 화살표 ->
  Product1/2/3)으로 보여주고, 하단 `Palette`에서 실제 모델의 물질/분포 아이콘(E, I, 1s, P,
  Q, R(s), T(s), empty)을 drag&drop으로 채워 넣으면 후보 스텝 목록이 자동으로 필터링된다.
  `Reset pattern` 버튼, 우측 `Filter` 아이콘 그룹(`s-depend`, `phase comp.`, `bal. counter`,
  `proportional`)으로 추가 필터링 가능.
- 더블클릭 또는 `Ok` → Reaction step 편집 다이얼로그:
  - `Name`(자유 서술), `Pattern`(선택된 템플릿의 일반형), `Result`(현재 입력값이 반영된
    구체적 반응식 미리보기, 예: `R(s)+E-->R(s+1), kp`)
  - `Educt(s)` / `Product(s)` 입력 상자: 클릭 시 컨텍스트에 맞는 물질/분포 선택 팝업이
    뜨고 클릭으로 채워짐(키보드 직접 입력도 가능)
  - `Coefficient(s)`: k1, (k2) - 각각 값/이름 선택
  - `Additional file(s)`: `File` - 스크립트를 계수에 연결(`k1(File)` 표기)
  - `Enthalpy`: `Value` 드롭다운 + `-DHr [kJ/mol]` 입력
  - `Diverse`: 기타 플래그
  - `Monte Carlo settings`: `index 1`~`index 6` 체크박스 (최대 2개 허용)
  - `Active` 체크박스 (스텝을 삭제하지 않고 on/off)
- 일반화(generalization) 개념: 예를 들어 `Propagation`(단일 결과) 대신 더 일반적인
  `Propagation(copolymer)`(두 개의 서로 다른 활성 사슬 이름을 허용) 템플릿을 선택할 수도
  있다. 튜토리얼은 "가장 일반적인 패턴을 항상 쓸 수도 있지만, 상황에 맞는 가장 단순한
  패턴을 쓰는 것이 더 편리하다"고 명시한다 - 즉 clone의 템플릿 카탈로그도 특수형과 일반형을
  모두 제공하고 사용자가 상황에 맞게 고르게 해야 한다.
- 자동 선언 확인 다이얼로그: 새 물질/분포/파라미터 이름을 입력하면 `Ok` 시
  "N objects will automatically be added to the model data: substance: E; parameter:
  k3" 형태의 확인창이 뜨고 `Ja`/`Nein`(Yes/No)으로 승인한다. 승인 후에도 새로 생성된
  항목은 기본값(0)만 채워진 "미완성" 상태이므로, 사용자가 반드시 해당 리스트로 가서
  값을 채우도록 UI가 안내해야 한다(clone에서는 draft 항목에 경고 배지 표시 권장).
- General kinetic step (`Kinetic` 패턴, PRESTO-KINETICS 스타일): 최대 5개 반응물
  (`A_i`)과 5개 생성물(`B_i`)을 지원하는 표 형태 입력.
  - 각 행: `n_i`(화학양론 계수), `A_i`(물질), `order_i`(반응 차수, 계수와 별도로 지정),
    중앙 `k_forw(File)` / `<--->` / `k_backw(File)` 열, `m_i`, `B_i`, `order_i`
  - 화학양론 계수와 반응 차수는 독립적으로 입력할 수 있어야 하며, `order_i`를 비워두면
    `order_i = n_i`로 자동 간주된다(튜토리얼의 Oregonator 4번째 스텝 `C -> B+D`가 실제로는
    2차(`r4 = k4*C^2`)로 요구되는 사례가 이를 보여준다).
  - `File [+Enthalpy]`, `Reaction law rp`(사용자 정의 rate law 스크립트), `Equilibrium`
    체크박스(체크 시 backward 파라미터 입력란이 `equilibrium constant`로 의미가 바뀜)

### 1.7 Recipe 다이얼로그

- 상단: `Name`, `Comment`, 대상 `Reactor` 탭들(다중 reactor 프로젝트의 경우 reactor별 탭)
- `Operation mode` 드롭다운(reactor의 기본 모드를 recipe에서 override 가능),
  `Temperature[C]`, `Pressure[bar]`, `Exit stream[l/s]`(드롭다운 + 값), 우측 `Tanks`
  아이콘(추가/복제/삭제)
- 탭 `Reactor input`:
  - `Composition of tank` 라벨
  - `Input as` 드롭다운 - 7가지 입력 모드: `Absolute masses`, `Mass parts and total
    mass`, `Absolute moles`, `Mole parts`, `Concentrations and volume`, `Mass parts and
    total mole number`, `Mole parts and total mass`
  - 표 컬럼: `Substances`, `Part (mass)`, `Masses [g]`, `Part (mole)`, `Moles`,
    `Concentration [mol/l]`, `Mole mass [g/mol]`, `Density [g/l]`
  - `Sum` 행과 `Volume [l]` 행이 하단에 표시됨. 선택한 `Input as` 모드에 따라 편집
    가능한 셀만 노란색으로 하이라이트되고 나머지는 자동 계산된다.
  - Consistency 공식: `1 = sum(c_i * M_i / rho_i)` (c: concentration, M: 분자량,
    rho: 밀도). 몰/질량 기반 입력이면 자동으로 이 식이 만족되지만, 그 외 입력(예:
    농도 직접 입력)은 `Sum` 값이 1이 아닐 수 있으며 이때 빨간색 숫자로 경고한다.
  - 두 가지 서로 다른 보정 액션(우클릭 팝업, 반드시 구분 구현):
    1. `Set concentration consistent` - 선택한 한 성분의 농도를 역산해서 전체 혼합비를
       1로 맞춘다 (예: 부피 변화가 큰 시스템에서 필수).
    2. `Set rest` - 아직 정의되지 않은 나머지 성분(주로 용매/희석제)에 남은 양을 채운다.
  - 밀도는 `T`, `p`에 의존하므로, `Reactor input` 탭의 `Temperature`를 먼저 확정해야
    정확한 consistency 계산이 가능하다는 점을 튜토리얼이 명시적으로 강조한다.
  - `Open substance` 우클릭 옵션으로 recipe 화면에서 바로 substance 편집 다이얼로그로
    이동 가능.
- 탭 `Feed_<TankName>` (continuous/semibatch에서 등장):
  - `Composition of tank` (별도 조성표, `Input as` 재선택 가능)
  - `use temperature [C]` 체크 + 값
  - `Feed type` 드롭다운: 예 `Mass stream, simple` + 값[g/s]
  - 표: `Time [s]`, `Mass stream [g/s]`, `Temperature [C]` (시간 종속 프로파일 입력 가능)
  - `Control`: `use feed control`(스크립트 참조), `use temperature control`(스크립트 참조),
    `Switch time [s]`
- `Exit` 서브 섹션: `Time [s]` vs `Exit [g]` 표 (배치 종료/배출 스케줄)
- 하단 버튼: `Process Control`(옵션), `Ok`/`Cancel`

### 1.8 Simulation Ribbon & 실행 제어

- `Debug mode` 체크박스(토글) - 활성화 시 스텝 실행마다 debug 창이 갱신되며 시뮬레이션이
  느려진다는 점을 명시.
- 컨트롤 버튼: `Show`(그래프 창 열기), `Start`, `1 Step`, `Stop`, `Restart`(실제로는 t=0으로
  reset). `Restart` 이후 다시 `Start`를 눌러야 실행된다.
- `Simulation end time` 입력창 + `Proc`(run-to-time) - 지정 시각까지만 적분 후 정지, 이후
  다시 입력해 이어서 실행 가능. 초기 반응 거동을 비교하는 데 필수적인 기능(예: t=0.1s까지만
  실행해 두 conversion 정의의 초기 차이를 확인).
- `Simulation mode` 라디오(`Distributions`/`Moments`) + `incl. Monte Carlo method` +
  `use tau leaping` + `full chain computation` 체크박스들이 같은 리본에 위치.
- `Actual values` 패널: `Time`, `No.`(스텝 번호), `Replay`, `#Variables`, `Stepsize` 컬럼 -
  적분기 스텝 이력을 그대로 노출하는 디버깅/성능 진단용 표.

### 1.9 Graphs (실시간 출력) 창

- 좌측 리스트: `Name`, `Type` 두 컬럼. `Type`은 `Substance`, `component`(reactor의 Mass/
  Vol/Temp/Pressure 등 스칼라 변수), `Distribution`, 이후 스크립트를 출력으로 등록하면
  `Output variable`이 추가된다.
- `Graphic update after n steps, n =` 스핀박스 - 매 스텝 그리지 않고 n스텝마다 갱신해 대량
  스텝 시뮬레이션의 렌더링 부하를 줄인다.
- `Show graphic data` 체크 - 켜면 그래프 옆에 원시 데이터 표(raw data table, X/Y 컬럼)가
  나타난다.
- 탭: `Standard`(기본 4분할 레이아웃) + 사용자 정의 탭(`New` 버튼으로 추가, `Rename`,
  `Delete all charts and close tab`, `Move left`/`Move right`).
- Drag&drop으로 좌측 리스트 항목을 캔버스에 끌어놓으면 새 chart가 생기고, 이미 있는
  chart 위에 다시 끌어놓으면 같은 chart에 curve가 추가(overlay)된다. 이 "겹쳐 그리기"
  상호작용이 clone GUI에서 반드시 재현되어야 하는 핵심 UX다.
- 개별 chart 우클릭 메뉴: `Info`, `Save graphic data...`, `Load graphic data...`,
  `Load GPC data ...`, `Save graphic data in mdf-file`, `Chart to Excel`, `Edit chart ...`,
  `Edit <name>`(방정식/스크립트 편집 바로가기), `Edit script (*.fun)`, `Close`, `Proceed`,
  `Stop`.
  - `.dat` 저장/불러오기: 동일 프로젝트 내 reference curve로 재사용(예: moment 모드 결과를
    `mn.dat`/`mw.dat`로 저장 후 distribution 모드 결과와 겹쳐 비교).
  - `Load GPC data ...`: 실험 GPC 곡선을 별도 포맷으로 불러오는 전용 로더 - 일반 `.dat`
    로더와 구분되는 기능이므로 clone에서도 "reference curve"와 "experimental GPC import"를
    분리된 기능으로 설계해야 한다.
  - `Save graphic data in mdf-file`: 별도 바이너리/구조화 포맷(MDF) 저장 - clone에서는
    이를 HDF5/NPZ로 대체해도 무방하나 "구조화된 원시 데이터 저장"이라는 요구는 유지한다.
- `Info` 팝업 (`Components information board`): `Component`, `Type`(`dist1d` 등),
  `Value type`(Concentration [mol/l], Concentration [g/l], Number-average Mn [g/mol],
  Weight-average Mw [g/mol], Dispersity, Ref. volume: main, Last value), `Value`, `Unit`.
  즉 분포 하나에서도 여러 파생 스칼라(Mn/Mw/PDI/농도 2종/기준 부피/최근값)를 한 번에
  조회할 수 있는 요약 패널이 필요하다.

### 1.10 Chart Administration 다이얼로그

- 좌측 패널 `Charts on pages`: `No.`, `A(ctive)`, `Name`, `Page`, `SI`, `A...` 컬럼의
  전체 chart 목록. 추가/재정렬/복제/페이지 아이콘 툴바.
- 우측 패널 `Graphs in chart`: 좌측에서 선택한 chart 안에 들어있는 curve 목록
  (`No.`, `A`, `Graph`, `C`, `Type`, `Source`, `Chart`).
- 하단 탭 `General` / `Optical` / `Points`:
  - `General` 탭 핵심 라디오: `Distribution graphic` / `Moment graphic` /
    `Monte Carlo method`(비활성 시 회색)
    - `Distribution graphic` 선택 시 `y-axis`: `concentration` / `weight` / `GPC`
      (아래 참고), `x-axis`: `chain length` / `molmass`, 추가 `x-axis` 라디오:
      `linear` / `logarithmic`
    - `Moment graphic` 선택 시 `y-axis`: `Mn` / `Mw` / `concentration` / `dispersity`,
      `x-axis`: `time/pos`
    - `Monte Carlo method` 선택 시 `Index 1..6` 라디오 + `Type`: `relative`/`absolute`
  - GPC 표현식: 분포 `P(s)`를 GPC 스타일로 그릴 때는 `W(log M) 는 P(s) * s^2`에 비례
    (사슬길이의 제곱 가중)로 그린다. 튜토리얼은 이 가중 때문에 사슬길이 축 끝단의
    아주 작은 농도값도 크게 증폭되어, 수치 그리드가 고분자량 영역을 충분히 정밀하게
    잡지 못하면 GPC 곡선이 0으로 수렴하지 않는 아티팩트가 나타남을 실제로 보여준다
    (`P(s)` 자체는 사실상 0인데 `s^2` 가중 후 곡선이 완전히 0으로 떨어지지 않는 사례).
    이 문제는 `Numerics` 탭의 `Error weighting according to distribution type`을
    `GPC [very high disp.]`(또는 `Weight [high disp.] /GPC [low disp.]`) 로 바꿔
    고분자량 tail의 오차를 더 엄격히 통제해야 해결된다. clone의 h-p 오차 추정자도
    "출력 표현식(농도/weight/GPC) 별 가중치"를 반영할 수 있어야 하며, 단순히 L2 오차만
    보면 GPC 표현에서 tail 정확도가 부족해질 수 있다는 점을 core error_estimator 설계에
    반영해야 한다.
- `Average curves`, `Comment`, `Page : Sorting Index` 하단 입력.

### 1.11 Numerics 탭

- `Accuracy`: `Type` 드롭다운(`Constant`/`File`/`Adapted`) + `Value`
- `Numerical option` 표: `Actual stepsize`, `Maximum stepsize`, `Initial stepsize`,
  `Scaling`, `Implicit scaling`, `Cut of negative concentrations`, `Consistency check`,
  `Solver`(예: `MET(2) [stiff]`), `Error weighting according to distribution type`
  (`Concentration` / `Weight [high disp.]` / `GPC [low disp.]` /
  `Weight [high disp.] /GPC [low disp.]` / `GPC [very high disp.]`),
  `Chain-length strategy according to problem type`,
  `Accuracy (distributions) according to problem type`
- `Set default values`, `Update` 버튼.

### 1.12 Script / Interpreter 편집기

- 상단: `Name`, 코드 편집 영역(여러 줄), `Syntax` 버튼 + "Syntax okay"/에러 메시지,
  `Line:` 표시, `Set` 버튼.
- 우측 확장 패널 탭: `Template`, `Functions`, `Species`, `Distributions`, `Parameters`,
  `Procedures`, `Reactors`, `Profiles`.
  - `Filter by string`, `Filter by type` 두 개의 필터 컨트롤.
  - `Functions` 탭: 함수 목록(컬럼 `No., Name, 1.Arg, 2.Arg, ...`) + 하단에 시그니처와
    한 줄 설명(예: `getx("substance") - given a species, return value is the
    conversion`).
  - `Species`/`Distributions`/`Parameters`/`Reactors`/`Profiles` 탭: 현재 프로젝트에 정의된
    이름 목록 - 더블클릭 또는 drag&drop으로 편집 중인 코드에 이름이 삽입된다.
  - `Template` 탭: 컨텍스트(예: 반응 스텝의 backward/forward 계수 자리)에 맞는 스텝별
    boilerplate 코드가 자동 표시되고, 우측 체크리스트(관련 elemental species/parameter
    이름들, 예: `E`, `I`, `Is`, `R_1:Temp`, `R_1:Mass`, `R_1:Vol`, `R_1:Pressure`, `kd`,
    `kp`, `ktc`, `ktd`, `0`)에서 체크한 항목만큼 `getco(...)`/`getkp(...)` 호출문이
    자동 삽입된다. `Apply template` 버튼으로 코드 편집 영역에 반영.
- 실제 확인된 함수 카탈로그 (Filter by type = substance/parameter/distribution 별):
  - `getco(substance)` - 현재 몰농도
  - `getcf(substance)` - feed 관련 농도로 추정 (원문 설명 미상, TODO 표시하고 구현 시
    실제 필요에 맞게 재정의)
  - `getconsum(substance)` - 누적 소비량류 값으로 추정 (TODO 확인)
  - `getcoini(substance)` - 초기 농도
  - `addvalue(substance, number)` - 값 누적/추가
  - `getuxr(profile, number, number, substance)` - PDE profile 관련 (후순위, PDE 지원
    범위에서 재정의)
  - `getx(substance)` - built-in conversion (input, feed, exit을 반영한 누적 전환율).
    공식: `X_A(t) = 1 - [적분항 + A(t)V(t)] / [A(0)V(0) + feed 적분항]`
  - `getmy(distribution, order)` - 분포의 order차 통계 모멘트 (order = 1,2,3)
  - `weightedmy(distribution, number, function...)` - 가중 모멘트 (후순위)
  - `getkp(parameter)` - 현재 반응계수 값 조회 (Arrhenius 평가 후 값 포함)
  - `getkpreac(parameter, reactor)` - reactor별 반응계수 조회
  - `setkp(parameter, number)` - 반응계수 값을 스크립트에서 직접 설정 (온라인 변경,
    `online-change allowed` 플래그와 연동)
  - `getkpt(parameter, number)`, `getkptp(parameter, number, number)` - 시간/추가 인자
    버전의 반응계수 조회 (후순위)
  - `gettotalmy(reactor, order)` - reactor 내 모든 고분자 분포의 모멘트 합산 - 개별
    분포 이름을 일일이 나열하지 않고 reactor 단위로 총 모멘트를 얻는 편의 함수. 다중
    사슬 종(예: 공중합/분지 모델에서 활성/비활성 사슬이 여러 개)일 때 필수.
  - Interpreter의 일반 원칙: `get*` 계열 함수로 값을 읽고, `result1`, `result2`, ... 로
    반환값을 지정하며, 자동 인자는 `arg1`, `arg2`, ... 로 주어진다. 별도의 타입 선언 없이
    좌변에 등장한 이름은 그 이후 우변에서 자유롭게 재사용 가능(약한 타입의 절차적 스크립트
    언어).
- Script를 output으로 등록: 그래프 아이콘 클릭 → `Library` 탭에 새 `Output variable`
  생성 → 좌측 Graphs 리스트에도 자동 반영되어 다른 output들과 동일하게 drag&drop 가능.
- Script를 반응 계수 modifier로 등록: 반응 스텝 다이얼로그의 `File` 입력 옆
  `...`(ellipsis) 버튼 → `Script selection` 팝업(기존 스크립트 목록 + `New`) → 선택/작성.
  - `k1(File)` 표기: 스크립트 결과가 원래 파라미터 값을 대체
  - `k1*File` 표기: 스크립트 결과가 원래 파라미터 값에 곱해짐
  - 결과가 2개 필요한 스텝(예: Combination/Disproportionation의 `ktc`, `ktd`)은
    `result1`, `result2`를 모두 채워야 하며, Template 탭이 이 요구사항(두 개의 결과)을
    자동으로 반영해 boilerplate를 만들어준다.
- Script report (`Script Report` 탭): 프로젝트 내 모든 스크립트 목록
  (`No., Name, Error, Debug, Type, File, Used in`) - 특정 스크립트가 어디에서 쓰이는지
  (`library variable X; Graphical line in ...`, `reaction step Y`) 역추적 가능. 이는
  코드 중복(예: 동일한 viscosity 계산을 output 스크립트와 반응계수 스크립트에 따로
  작성해 유지보수 리스크가 생기는 것)을 사용자가 스스로 인지하게 돕는 진단 도구다.
  튜토리얼도 이 중복 문제를 명시적으로 지적하며, "procedure"(서브루틴) 기능으로 해결
  가능하다고 언급한다 → clone에서는 procedure/서브스크립트 재사용 기능을 M27~M28
  범위에 포함해 이 중복 문제를 원천적으로 줄이는 것을 목표로 한다(원본보다 개선점).

### 1.13 Script Debugger

- `Debug mode` 체크 후 `Restart` → 시뮬레이션을 다시 0에서 시작하며 debug 창이 자동으로 뜬다.
- Debug 창 상단에 선택된 스크립트별 탭 버튼(예: `Glass effect`, `Gel effect`)이 표시되고,
  `+`/`-` 아이콘으로 디버그 대상 스크립트를 추가/제거할 수 있다.
- 본문 표: `Line`, `Text`(코드 라인), `Assignment/Condition`(예: `Assignm: kp0 =`),
  `Value`(그 시점의 실제 값) - 라인 단위 실행 추적.
- 컨트롤: `1 Step`(정확히 한 스텝 진행), `Proc`(지정된 `Simulation end time`까지 실행),
  `Stop`, `Restart`.
- 우클릭 `Edit script` → 즉시 해당 스크립트 편집기로 이동. 단, 수정한 스크립트는
  `Restart` 이후 재시뮬레이션에서만 반영된다(현재 실행 중인 시뮬레이션에는 즉시
  반영되지 않음) - 이 제약을 clone에서도 명확히 지키거나, 개선하려면 "핫 리로드는 다음
  스텝부터 적용" 같은 명시적 규칙을 사용자에게 안내해야 한다.
- `Reactor:` 라벨과 진행률 바(현재 적분 시각/목표 시각)가 하단에 표시됨.

### 1.14 Advanced Model Generation

- Copolymerization assistant: `Number of monomers` 입력 + 체크박스형 반응 시스템
  선택(`Initiation`, `Propagation` - `Reaction coefficients: r-values`/`Constants`,
  `Copolymerisation: Monomer`/`Terminal model`; `Transfer`; `Termination` -
  `Reaction coefficients: Single pair ktc,ktd`/`Each ktc,ktd`), `Solvent`
  (`Add solvent`, `Transfer to solvent`), `Balance variables`(`No`/`Per monomer`/
  `Diades`), `Create`/`Cancel`. 단량체 수를 1로 설정하면 동종중합 모델도 이 assistant로
  생성 가능하다는 점이 튜토리얼에서 실제로 시연된다 - 즉 assistant는 "동종중합의 특수
  케이스로서의 공중합"이라는 일관된 내부 모델을 사용한다.
- Mark equal components: 우측 상단 토글 - 켠 상태에서 한 컴포넌트를 클릭하면 같은
  이름이 쓰인 다른 위치(반응 스텝, recipe 등)가 색칠되어 하이라이트된다.
- 구조 네트워크 그래프: 원본은 외부 프로그램 Wingraphviz가 설치되어 있어야
  동작한다. clone에서는 외부 바이너리 의존 없이 Python 생태계(graphviz 파이썬
  바인딩 또는 networkx+matplotlib)로 반응 스킴 그래프를 그리는 내장 뷰를 제공한다
  (비목표 섹션에 명시).
- Group 관리: 컴포넌트 편집 다이얼로그의 `Group` 필드에 자유 텍스트를 입력하면 그룹이
  생성되고, drag&drop으로 여러 컴포넌트를 한 그룹에 다중 배정할 수 있다. 좌측 내비게이션의
  `Group filter` 패널에서 그룹별로 필터링해 대형 모델을 탐색한다.

### 1.15 PRESTO-KINETICS / Oregonator 튜토리얼에서 확인된 추가 사항

- 이 튜토리얼은 분포/고분자 없이 원소 종(elemental species)만으로 구성된 일반 화학
  반응계를 다룬다. clone의 M30 general kinetic engine이 이 케이스의 기준 reference다.
- Substance 다이얼로그가 재사용되지만 `Molmass = 0`(미입력)도 허용되며, 이 경우 clone은
  질량 균형 계산을 건너뛰고 경고만 표시해야 한다(원문: "PRESTO-KINETICS will check
  the mass balance of a reaction step and give a warning if violated").
- 숫자 상수(`0`, `2`)를 이름 그대로 parameter로 자동 등록하는 흐름이 Oregonator
  튜토리얼에서 두 번(역반응 계수 `0`, 화학양론 계수 `2`) 반복 확인된다 - M24/M30에서
  숫자 리터럴 자동 파라미터화는 필수 요구사항으로 재확인.
  - `2` 입력 시 `k_forw` 열이 아니라 화학양론 계수(`m_i`) 자리에 입력되며, `Ok` 시
    자동으로 `parameter: "2"`가 생성된다는 점에 유의 - 즉 화학양론 계수 자리와 반응
    계수 자리 모두 "숫자 리터럴 → named parameter 자동 승격" 규칙이 동일하게 적용된다.
- `Restart` 의미가 "실제로는 초기화(reset to t=0)"라는 점이 두 튜토리얼 모두에서
  동일하게 강조된다.
- 출력 스텝 스로틀링의 실질적 효과: Oregonator는 282 스텝까지 필요했고, 그래프를 매
  스텝 갱신하면 시뮬레이션이 "느려 보이지만 실제로는 그래픽 출력이 병목"이라는 점을
  명시. `n=10` 스텝마다만 갱신하도록 바꾸면 수 초 내 종료됨을 보여준다 → clone의
  `SimulationWorker`도 그래픽 콜백을 매 스텝이 아니라 throttle 옵션으로 노출해야 한다
  (`plan.md`/`plan3.md`의 배치 업데이트 요구사항과 일치, 이번 튜토리얼에서 정량적으로
  재확인됨).

---

## 2. 현재 구현 대비 Gap (plan4.md 대비 갱신)

`plan4.md` 2절의 gap 목록은 대체로 유효하다. 이번 재검토로 다음을 추가/수정한다.

### 2.1 모델 입력 workflow gap (추가)

- Substance/Distribution 다이얼로그가 "이름 + 분자량" 수준이면 부족하다. phase
  setting(Main/Own/Reactive), density 선형식, heat capacity 다항식, output 노출 플래그
  까지 스키마에 반영해야 recipe consistency 계산(1.7절)이 성립한다.
- Parameter가 단순 스칼라만 지원하면 부족하다. Arrhenius 식의 기준온도/기준reactor/
  활성화부피(DV/R) 필드까지 필요하다 (다중 reactor cascade에서 reactor별 온도 참조가
  실제로 쓰임).
- 반응 스텝의 화학양론 계수와 반응 차수(order)를 별도 필드로 지원하지 않으면 Oregonator
  튜토리얼을 재현할 수 없다. 이는 plan4.md M30에서 이미 스키마에 `order`가 있었으나,
  "order 미입력 시 stoichiometric factor로 자동 대체"라는 기본값 규칙이 명시돼 있지
  않았다 - 이번 개정에서 명시.

### 2.2 Recipe gap (추가)

- consistency 보정에 두 가지 서로 다른 동작(`Set concentration consistent` vs
  `Set rest`)이 있다는 점이 plan4.md에는 빠져 있었다. 단일 "auto-fix" 액션으로 뭉뚱그리면
  튜토리얼의 실제 사용 패턴(용매로 나머지를 채우는 것과, 한 성분의 농도를 역산하는 것은
  다른 상황)을 재현하지 못한다.
- 밀도가 온도에 종속적이므로 recipe consistency 계산 순서(온도 확정 → 밀도 평가 →
  consistency 계산)를 엔진 레벨에서 강제해야 한다.

### 2.3 Chart/output workflow gap (추가)

- GPC 표현(`P(s)*s^2` 가중)이 단순 y-axis 옵션이 아니라, 수치 오차 추정자와 직접
  연결된 문제임이 튜토리얼에서 실증된다(1.10절). plan4.md M26은 이를 순수 GUI 기능으로만
  다뤘으나, 실제로는 `core/error_estimator.py`(plan.md/plan3.md의 backend)가 "출력
  표현식별 가중 오차"를 지원해야 GPC tail이 정확해진다 - M26과 core 팀 사이의 인터페이스
  요구사항으로 별도 명시 필요.
- reference 데이터에 `.dat`(단순 curve), `mdf-file`(구조화 저장), `GPC data`(실험 GPC
  임포트) 세 가지 서로 다른 저장/불러오기 경로가 있다. 단일 "export/import" 기능으로
  뭉뚱그리지 않는다.
- `Components information board`(Info 팝업)처럼 분포 하나에서 Mn/Mw/PDI/농도(mol,g)/
  기준부피/최근값을 한 번에 조회하는 요약 패널이 필요하다.

### 2.4 Script interpreter gap (추가)

- 함수 alias 목록이 plan4.md에는 4개(`getx/getco/getmy/getkp`)뿐이었으나 실제로는 최소
  10개 이상 확인된다(1.12절). 전부를 1차 구현 대상으로 삼을 필요는 없지만, 함수 카탈로그
  UI(필터+설명+drag&drop 삽입) 자체는 1차 구현 대상이어야 한다 - 새 함수를 추가할 때
  UI 변경 없이 카탈로그 데이터만 늘리면 되는 구조가 바람직하다.
- Template 자동생성 기능(체크리스트 기반 boilerplate)이 plan4.md에는 없었다.
  스크립트 작성 진입장벽을 낮추는 핵심 기능이므로 M27/M28에 추가한다.
- 코드 중복 문제(같은 계산을 output 스크립트와 반응계수 스크립트에 각각 작성)를
  원문은 "procedure로 해결 가능하나 이 튜토리얼에서는 다루지 않는다"고 명시적으로
  인정한다. clone은 이를 개선 기회로 삼아 procedure(서브스크립트) 기능을 1차
  스코프에 포함한다.

### 2.5 General kinetic model gap (추가)

- 화학양론 계수 자리에 숫자 리터럴을 입력해도 named parameter로 자동 승격되는 규칙이
  반응 계수 자리와 동일하게 적용되어야 한다(1.15절).
- `Molmass = 0`(미입력) 허용 + soft mass-balance warning 정책이 재확인됨.

### 2.6 Tutorial/reproducibility gap (변경 없음, 유지)

### 2.7 신규: Simulation mode 및 실행 제어 gap

- `Distributions`/`Moments` 전역 토글, run-to-time(`Simulation end time` + `Proc`),
  `Actual values`(스텝 이력 표) 진단 패널이 plan4.md에는 전혀 없었다. 이는 M29(디버거)와
  별개로 엔진 실행 제어(run control) 자체의 기능 요구사항이므로 신규 마일스톤(M32)으로
  분리한다.

---

## 3. Plan4(Revised) 목표

`plan4.md`의 세 가지 목표(Tutorial Reproducibility / Guided Modeling Workflow /
Interactive Analysis Workflow)를 유지하되, 다음을 추가한다.

4. Numerical-UI Consistency
   - GPC/moment 등 "출력 표현식"이 단순 그래프 옵션이 아니라 core 오차 추정 정책과
     연결되어야 함을 인식하고, GUI 설정이 실제로 core 파라미터에 반영되게 한다.

5. Reduced Duplication vs Original
   - 원본이 인정한 한계(스크립트 중복)를 procedure 기능으로 개선한다.

---

## 4. Milestone Roadmap (Revised)

| 단계 | 목표 | 주요 산출물 | 검증 |
| --- | --- | --- | --- |
| M22 | Tutorial project templates | polyethylene, Oregonator sample projects (Molmass=0 허용 포함) | project load/run tests |
| M23 | Species/Distribution/Parameter administration (필드 확장) | phase setting, density/heat-capacity 스키마, Arrhenius 기준reactor/온도, numeric-literal-as-parameter 규칙 | schema roundtrip, GUI edit tests |
| M24 | PatternFinder-style reaction builder (필터+drag&drop+자동선언 확인) | template catalog, pattern preview, 5x5 general kinetic step(order 기본값 규칙 포함), Ja/Nein 확인 다이얼로그 | reaction builder tests |
| M25 | Recipe consistency workflow (2가지 보정 액션 구분) | mole/mass/concentration 7-모드 입력, `Set concentration consistent`/`Set rest`, feed tank/Exit 스케줄 | recipe consistency tests |
| M26 | Chart administration + GPC-aware error weighting | 2-pane chart admin, GPC/`.dat`/`mdf`/GPC-import 3-way 데이터 경로, Info 패널, core error_estimator 연동 | GUI chart workflow tests + core weighting test |
| M27 | Script command compatibility + Template 생성기 | 함수 카탈로그(10+), Template 체크리스트, procedure(서브스크립트) 기초 | scripted output tests |
| M28 | Script-driven reaction modifiers + procedure 재사용 | `k(File)`, `k*File`, multi-result, procedure 호출 | kinetic modifier tests |
| M29 | Script debugger and run control (다중 스크립트 탭) | step-by-step, run-to-time, 다중 탭 debug 창, edit-in-place(+Restart 규칙) | worker/debug tests |
| M30 | General kinetic model support (order != stoichiometry, numeric literal 자동화) | Oregonator engine, soft mass-balance warning | Oregonator benchmark |
| M31 | Tutorial manual and regression suite | tutorial docs, generated example outputs | Sphinx build, tutorial smoke |
| M32 (신규) | Simulation mode & run-control | `Distributions`/`Moments` 전역 토글, `Actual values` 스텝 이력 패널, run-to-time 엔진 API | run-control tests |

---

## 5. Detailed Implementation Plan (개정 반영분만 발췌)

`plan4.md`의 M22~M31 상세 섹션은 대부분 유효하므로 전체를 재작성하지 않고, 이번
재검토로 바뀐 부분만 아래에 명시한다. 언급되지 않은 하위 항목은 `plan4.md` 원문을
그대로 따른다.

### M22 (변경)

- 추가 요구사항: `oregonator_kinetics_project()`에서 `Molmass`를 아예 설정하지 않는
  경로를 테스트에 포함한다 (soft warning만 발생, 실행은 막지 않음).

### M23 (확장)

`Substance`/`PolymerSpecies`/`Parameter` 스키마에 다음 필드를 추가한다.

```python
class ThermodynamicData:
    density_mode: Literal["linear", "function", "database"]
    density_linear_a: float | None  # rho = a - T * b
    density_linear_b: float | None
    heat_capacity_coeffs: tuple[float, float, float, float] | None
    heat_capacity_kelvin: bool

class Substance:
    phase_setting: Literal["main", "own", "reactive"]
    output_console: bool
    output_overview: bool
    thermo: ThermodynamicData

class PolymerSpecies(Substance):
    monomer_molar_mass: float
    ignore_copolymer_balance: bool
    s_min_zero: bool
    is_oligomer: bool
    max_chain_length: int | None
    monte_carlo_ensemble_size: int = 100

class Parameter:
    arrhenius_ref_temperature: float | None
    arrhenius_ref_reactor: str | None
    arrhenius_dv_over_r: float | None
    online_change_allowed: bool = False
    used_in_optimization: bool = False
```

- 숫자 리터럴 자동 파라미터화 규칙을 공용 유틸리티로 구현한다:
  `resolve_or_create_parameter(name_or_number)` - 이름이 숫자로 파싱되면 그 값으로
  parameter를 자동 생성(이미 있으면 재사용)하고, Ja/Nein 확인 다이얼로그에 노출한다.

### M24 (확장)

- Reaction step modules 카탈로그에 `Flow`, `Moment's cl.`, `Copolymeriz.`, `Profile`,
  `Balance` 속성 컬럼을 추가하고, 필터 탭(`Standard`/`Copolymerization`/`Special 1`/
  `Flow`/`Phases`/`Profiles`/`Balance`/`Used in model`)을 구현한다.
- PatternFinder drag&drop UI: 팔레트에서 물질/분포 아이콘을 Educt/Product 슬롯으로
  끌어놓으면 후보 템플릿 리스트가 실시간으로 필터링되는 서비스 레이어를 GUI와 분리해
  구현한다(`reaction_pattern_finder.py`).
- 일반 kinetic step 스키마에 `order` 기본값 규칙을 명시한다:

```python
class KineticTerm:
    species: str
    stoichiometric_factor: str  # parameter name (숫자면 자동 파라미터화)
    order: str | None = None    # None이면 stoichiometric_factor와 동일하게 처리
```

- 자동 선언 확인 다이얼로그는 생성될 객체 목록(`substance: E`, `parameter: k3` 등)을
  그대로 나열하고 Ja/Nein으로 승인받는다. 승인 후 생성된 draft 객체는 값 미설정 경고
  배지를 부여한다.

### M25 (확장)

- Recipe 입력 모드 7종을 전부 스키마/서비스 레벨에서 지원한다:
  `absolute_mass`, `mass_part_total_mass`, `absolute_mole`, `mole_part`,
  `concentration_and_volume`, `mass_part_total_mole`, `mole_part_total_mass`.
- consistency 서비스에 두 개의 개별 API를 둔다:
  - `make_concentration_consistent(recipe, target_substance)`
  - `fill_remainder(recipe, target_substance)`
- 밀도 평가는 반드시 `temperature`, `pressure` 확정 이후에 수행하도록 순서를 강제한다
  (엔진 레벨 assertion 또는 단계적 계산 파이프라인으로 구현).
- Feed tank 스키마에 `feed_type`(`mass_stream_simple` 등), 시간-종속
  `(time, mass_stream, temperature)` 테이블, `use_feed_control`/`use_temperature_control`
  스크립트 참조, `switch_time`을 추가한다.

### M26 (확장)

- `ChartConfig`에 다음을 추가한다.

```python
class ChartConfig:
    graphic_mode: Literal["distribution", "moment", "monte_carlo"]
    distribution_y_axis: Literal["concentration", "weight", "gpc"] | None
    x_axis_kind: Literal["chain_length", "molmass"] | None
    x_axis_scale: Literal["linear", "logarithmic"] = "linear"
    moment_y_axis: Literal["mn", "mw", "concentration", "dispersity"] | None
    monte_carlo_index: int | None
    monte_carlo_type: Literal["relative", "absolute"] | None
```

- GPC y-axis 선택 시 `W(log M) = P(s) * s^2` (또는 `s*Mmono`로 log(M) 축 변환) 계산을
  postprocess 레이어에 명시적으로 구현하고, 이 모드가 활성화되면
  `core.error_estimator`에 `weighting="gpc_tail"` 힌트를 전달해 고분자량 tail 오차
  기준을 강화한다. (core/GUI 인터페이스 계약을 `docs/`에 별도 기록)
- Reference 데이터 경로 3종을 분리 구현한다: `save_reference_curve`/`load_reference_curve`
  (`.dat` 상당), `save_structured_dump`(`mdf` 상당, 실제로는 HDF5/NPZ), `import_gpc_data`
  (실험 GPC 포맷 전용 파서, 초기에는 2-column CSV로 단순화 가능).
- `Components information board` 대응 GUI: 분포/물질 선택 시 요약 패널
  (`concentration_mol`, `concentration_mass`, `mn`, `mw`, `dispersity`,
  `reference_volume`, `last_value`)을 인스펙터에 표시한다.

### M27 (확장)

- 함수 카탈로그를 데이터 기반으로 구현한다 (`script/function_catalog.py`): 이름, 인자
  스키마, 설명, 카테고리(substance/parameter/distribution/reactor)를 테이블로 관리하고
  GUI는 이 테이블을 그대로 렌더링한다. 최소 구현 대상: `getx`, `getco`, `getcoini`,
  `getmy`, `gettotalmy`, `getkp`, `setkp`, `getcf`, `getconsum`. 나머지는 스텁 + TODO로
  남기고 카탈로그에는 "미구현" 배지로 표시한다.
- Template 생성기: 컨텍스트(반응 스텝 종류, 결과 개수)에 따라 boilerplate 코드를
  생성하는 `script_template.py`. 체크리스트로 선택된 species/parameter마다
  `x = getco("x")` / `k = getkp("k")` 라인을 자동 삽입하고, 결과 슬롯 수만큼
  `result1 = ...`, `result2 = ...`을 생성한다.
- Procedure(서브스크립트) 기초: 이름 있는 서브루틴을 정의하고 여러 스크립트에서
  호출할 수 있게 한다 (안전한 AST 서브셋 내에서 함수 정의/호출만 허용, 재귀/외부 호출
  금지). Gel/Glass effect 예제를 procedure로 리팩터링해 중복을 제거하는 예제를 포함한다.

### M28 (확장)

- 반응 스텝의 multi-result modifier(`result1`, `result2`)가 Combination/Disproportionation
  같은 2-계수 스텝에 정확히 매핑되는지 검증하는 계약 테스트를 추가한다.
- procedure를 output 스크립트와 반응계수 스크립트 양쪽에서 공유하는 통합 테스트를
  추가해 "원본의 코드 중복 한계"가 clone에서는 재현되지 않음을 회귀 테스트로 고정한다.

### M29 (확장)

- Debug 창을 다중 스크립트 탭 구조로 구현한다: 활성 디버그 대상 스크립트 목록을
  `+`/`-`로 관리하고, 각 탭은 독립적인 실행 추적 표(`line, text, assignment, value`)를
  가진다.
- `Edit script` 진입 시 "수정 사항은 Restart 이후 적용됨"을 명시적으로 안내하는 UI 문구를
  포함한다.
- `run_to_time(t)`와 `single_step()`을 `SimulationEngine`의 정식 API로 노출하고, GUI의
  `Proc`/`1 Step` 버튼이 이를 그대로 호출하게 한다(M32와 API 공유).

### M30 (확장)

- `Molmass` 미설정(0 또는 None) substance를 허용하고, 이 경우 mass-balance 검사를
  건너뛰며 "mass balance skipped: substance X has no molecular weight" 경고를 낸다.
- 화학양론 계수 자리의 숫자 리터럴도 M23의 `resolve_or_create_parameter` 규칙을 그대로
  적용해 named parameter로 자동 승격한다.
- order 기본값 규칙(M24절)이 general kinetic 엔진에도 동일하게 적용되는지 Oregonator
  4번째 스텝(`C -> B+D`, order=2)을 회귀 테스트로 고정한다.

### M31 (변경 없음, 유지)

`plan4.md` 원문의 매뉴얼/회귀 스위트 계획을 그대로 따르되, 신규 M32 관련 매뉴얼 페이지
(`manual/tutorial_run_control.rst`)를 추가한다.

---

### M32 (신규). Simulation Mode & Run Control

#### Scope

`Distributions`/`Moments` 전역 시뮬레이션 모드 토글과, run-to-time/step 기반 실행 제어를
엔진과 GUI 양쪽에 정식 기능으로 추가한다.

#### Engine Requirements

- `SimulationRequest`에 `mode: Literal["distributions", "moments"]` 필드를 추가한다.
  - `moments` 모드는 core Galerkin PBE 대신 모멘트 폐포 ODE(`core/moments.py`의 closure
    식 활용)만 적분해 빠른 근사 결과를 낸다.
  - `distributions` 모드는 기존 전체 PBE 경로를 사용한다.
- `SimulationEngine.run_to_time(t)`, `SimulationEngine.single_step()` API를 추가한다
  (M29와 공유).
- `SimulationResult`에 스텝 이력 메타데이터(`step_index`, `time`, `stepsize`,
  `n_variables`)를 배열로 저장해 `Actual values` 패널 데이터 소스로 쓴다.

#### GUI Requirements

- Simulation 탭 상단에 `Distributions`/`Moments` 라디오 + `incl. Monte Carlo method`
  (후순위 스텁) 체크박스를 추가한다.
- `Simulation end time` 입력 + `Proc` 버튼(run-to-time), `1 Step` 버튼을 Simulation
  Panel에 노출한다.
- `Actual values` 표를 Simulation 탭 하단 또는 별도 dock으로 제공한다.
- Moments 모드로 저장한 결과를 Distributions 모드 결과 위에 reference curve로 겹쳐 그리는
  워크플로를 튜토리얼 예제(`examples/tutorial_polyethylene_basic.py`)에 포함한다.

#### Acceptance Criteria

- 동일 프로젝트를 `moments` 모드와 `distributions` 모드로 각각 실행했을 때, `Mn`/`Mw`
  궤적이 서로 근접함을 회귀 테스트로 확인한다(정확히 일치할 필요는 없으며 상대오차
  임계값으로 판정).
- `run_to_time(0.1)` 이후 재개(`run_to_time(final_time)`)했을 때 전체를 한 번에 실행한
  결과와 동일함을 확인한다.
- `Actual values` 패널이 스텝 수/스텝 크기 이력을 정확히 반영한다.

#### Tests

- `tests/test_simulation_modes.py` (moments vs distributions 근접성)
- `tests/test_run_control.py` (run_to_time/single_step/resume 일관성)
- GUI smoke test: 모드 토글 + Actual values 패널 렌더링

---

## 6. Implementation Order (Revised)

1. M22 tutorial project templates (Molmass=0 케이스 포함)
2. M30 general kinetic engine foundation (order 기본값 규칙 포함)
3. M32 simulation mode & run control 엔진 API (M29/GUI가 이후 이 API를 재사용하므로 먼저)
4. M24 reaction builder services (필터/자동선언, GUI 폴리시 이전)
5. M23 component administration 스키마 확장/GUI
6. M25 recipe consistency workflow (2-액션 구분)
7. M27 script command compatibility + template 생성기
8. M28 script-driven reaction modifiers + procedure
9. M26 chart administration + GPC-aware weighting (core 인터페이스 계약 포함)
10. M29 script debugger/run control GUI (M32 API 위에 구축)
11. M31 tutorial manual and regression suite

변경 사유: 원래 순서는 M26(chart)이 비교적 앞쪽이었으나, GPC 가중치 문제가 core
error_estimator와 얽혀 있음이 이번 재검토로 드러났기 때문에 core 인터페이스 계약을 먼저
정리할 시간을 벌기 위해 M26을 뒤로, 여러 GUI 기능이 공유하는 run-control API(M32)를
앞으로 옮겼다.

---

## 7. Verification Matrix (신규/변경분만)

| Requirement | Evidence |
| --- | --- |
| Molmass 미설정 substance 허용 + soft warning | `tests/test_general_kinetics.py::test_missing_molar_mass_warns` |
| order 기본값 = stoichiometric factor | `tests/test_general_kinetics.py::test_oregonator_order_override` |
| 숫자 리터럴 자동 파라미터화 (반응계수/화학양론 계수 모두) | `tests/test_reaction_builder.py::test_numeric_literal_promotion` |
| Recipe 2-액션 consistency 보정 구분 | `tests/test_recipe_consistency.py` |
| GPC y-axis 가중치가 core error_estimator에 전달됨 | `tests/test_chart_gpc_weighting.py` |
| reference curve / structured dump / GPC import 3-way 분리 | `tests/test_chart_reference_io.py` |
| 함수 카탈로그 데이터 기반 렌더링 | `tests/test_script_catalog.py` |
| Template 생성기 boilerplate 정확성 | `tests/test_script_template.py` |
| procedure 재사용으로 코드 중복 제거 | `tests/test_script_procedure.py` |
| 다중 스크립트 탭 debug 창 | GUI offscreen test |
| moments vs distributions 결과 근접성 | `tests/test_simulation_modes.py` |
| run_to_time/resume 일관성 | `tests/test_run_control.py` |

`plan4.md` 원문의 나머지 Verification Matrix 항목은 그대로 유효하다.

---

## 8. Non-Goals (변경분)

`plan4.md`의 Non-Goals를 유지하고 다음을 명시적으로 추가한다.

- Wingraphviz 등 외부 바이너리에 의존하지 않는다. 구조 네트워크 그래프는 Python
  생태계(graphviz 파이썬 바인딩 또는 networkx+matplotlib) 내장 구현으로 대체한다.
- MDF(구조화 저장 포맷) 자체를 바이트 호환으로 재현하지 않는다. 동등한 기능(구조화된
  원시 데이터 저장/조회)을 HDF5/NPZ로 제공한다.
- `weightedmy`, `getuxr`, `getkpt`, `getkptp` 등 PDE/가중모멘트 계열 함수의 완전한
  의미론은 1차 스코프에서 스텁으로 남긴다(1.12절 명시).

---

## 9. Risks and Mitigation (추가분)

### Risk: GPC 가중치 요구사항이 core/GUI 경계를 흐릿하게 만든다

Mitigation:

- `docs/interfaces/gpc_weighting_contract.md`로 core-GUI 계약을 별도 문서화한다.
- GUI는 "표현 모드"만 선택하고, 실제 가중치 계산은 core가 소유한다(단방향 의존성 유지).

### Risk: 스크립트 함수 카탈로그가 무한히 커진다

Mitigation:

- 1차 스코프 함수(M27절)만 완전 구현하고 나머지는 "미구현" 배지로 투명하게 노출한다.
- 카탈로그는 데이터 테이블로 관리해 신규 함수 추가가 GUI 코드 변경 없이 가능하게 한다.

### Risk: 두 가지 consistency 액션(Set concentration consistent / Set rest)의 사용자 혼동

Mitigation:

- 두 버튼에 서로 다른 아이콘과 짧은 설명 tooltip을 부여한다.
- 어떤 성분이 "정의되지 않음"(rest 대상)인지와 "consistency 위반"(concentration 대상)인지
  UI에서 시각적으로 구분한다(예: 회색 vs 빨간색 강조).

`plan4.md` 원문의 나머지 리스크 섹션은 그대로 유효하다.

---

## 10. Plan4(Revised) Completion Criteria

`plan4.md`의 1~10번 완료 조건을 유지하고 다음을 추가한다.

11. `Distributions`/`Moments` 전역 모드 토글과 run-to-time API가 엔진/GUI 양쪽에서
    동작하고 회귀 테스트가 통과한다 (M32).
12. Recipe consistency의 두 가지 보정 액션이 서비스/테스트 레벨에서 명확히 분리되어
    있다 (M25).
13. GPC 표현 모드 선택이 core error_estimator 가중치에 실제로 반영됨을 계약 테스트로
    확인한다 (M26).
14. 스크립트 procedure 재사용으로 gel/glass effect 예제의 코드 중복이 제거되어 있다
    (M27/M28).
15. 구조 네트워크 그래프가 외부 바이너리 없이 내장 기능으로 동작한다 (M22/M24 연계
    기능, 비목표 8절 참조).