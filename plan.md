# PREDICI 재구현 계획: Discrete Galerkin h-p 기반 중합 반응 시뮬레이터

## 0. 목표와 범위 정의

PREDICI(Wulkow, CiT GmbH)는 중합 반응기에서 사슬길이분포(CLD)/분자량분포(MWD)를
**population balance equation (PBE)** 로 모델링하고, 이를 **discrete Galerkin h-p 적응법**으로
푸는 소프트웨어입니다. 완전 재구현은 다음 4개 축을 모두 필요로 합니다.

1. **수치해석 코어**: discrete Galerkin h-p 방법 (사슬길이 방향 적응 유한요소/직교다항식)
2. **반응속도론 엔진**: 임의의 반응 스킴(개시/성장/이동/정지/분지/절단/공중합)을 모멘트가 아닌
   전체 분포에 대해 표현
3. **시간적분 & 커플링**: 저분자 종(ODE/DAE) + 분포(PBE)를 동시에 강건하게 적분
4. **반응기 모델 & 후처리**: batch/semi-batch/CSTR/PFR/cascade, 모멘트·MWD 시각화, 파라미터 피팅

> 참고 문헌 (핵심 수학적 근거):
> - M. Wulkow, "The simulation of molecular weight distributions in polymerization
>   processes using discrete Galerkin methods", Macromol. Theory Simul. 1996
> - Wulkow, "Numerical treatment of countable systems of ODEs" (discrete Galerkin, h-p)
> - Deuflhard/Nowak — extrapolation 적분기(LIMEX류)와의 결합

이 계획은 "논문 재현 + 소프트웨어화"를 전제로 하며, 단계별로 검증 가능한 마일스톤을 둡니다.

---

## 1. 아키텍처 개요

```
predici-clone/
├── core/
│   ├── basis.py          # 직교다항식 기저 (Legendre 등), p-계수 변환
│   ├── grid.py            # 사슬길이 방향 적응 mesh (h-refinement), leaf/interval 관리
│   ├── galerkin.py         # discrete Galerkin 연산자 조립 (질량행렬, 반응 텀 사영)
│   ├── moments.py           # 분포 ↔ 모멘트(Mn, Mw, PDI) 변환, 재구성
│   └── error_estimator.py  # h/p 적응을 위한 국소 오차 추정
├── kinetics/
│   ├── reaction.py         # 반응 스킴 DSL (개시/성장/이동/정지/분지 등)
│   ├── rate_terms.py        # 각 반응이 PBE에 기여하는 생성/소멸 텀을 Galerkin 연산자로 변환
│   └── species.py           # 저분자종 대수/미분방정식 정의
├── integrator/
│   ├── coupled_system.py   # PBE 계수 + 저분자 ODE를 하나의 DAE/ODE 시스템으로 결합
│   ├── stepper.py           # 적응 시간적분기 (BDF/Radau 또는 extrapolation)
│   └── jacobian.py          # sparse Jacobian (자동미분 또는 유한차분)
├── reactor/
│   ├── batch.py / semibatch.py / cstr.py / pfr.py / cascade.py
│   └── energy_balance.py   # (옵션) 비등온 반응기
├── postprocess/
│   ├── distribution_plot.py
│   ├── moments_report.py
│   └── fitting.py           # 파라미터 추정 (실험 MWD/모멘트 대비)
├── api/
│   └── scheme_loader.py     # 사용자가 반응 스킴/반응기 조건을 정의하는 입력 포맷 (YAML/JSON)
└── validation/
    ├── benchmarks/          # 문헌에 나온 해석해 및 PREDICI 결과와 비교
    └── test_cases/
```

**언어/스택 제안**: 프로토타입은 Python (NumPy/SciPy/Numba, sparse는 SciPy sparse, 자동미분은
JAX 또는 CasADi 고려) → 성능이 문제가 되는 커널(그리드 조립, Jacobian)은 이후 C++/Rust로 이식.
초기부터 C++로 가면 개발 속도가 크게 느려지므로 비추천.

---

## 2. 핵심 수학: Discrete Galerkin h-p 방법

사슬길이 `n`에 대한 개수밀도 `c(n,t)`를 국소적으로 다항식으로 근사:

- 사슬길이 축을 구간 `I_k = [n_k, n_{k+1}]` 들로 분할 (h-mesh)
- 각 구간에서 직교다항식(Legendre 등) 전개, 차수 `p_k` (p-적응)
- 반응 텀(성장, 정지, 이동, 분지)은 `n`에 대한 convolution/shift 연산자이므로,
  이를 각 기저함수에 사영(Galerkin projection)하여 계수 ODE로 변환
- 이산 사슬길이 영역(올리고머, n이 작은 영역)과 연속 근사 영역을 **매끄럽게 연결**하는 것이
  PREDICI 고유의 "discrete-continuous" 처리 핵심 → 저차 n은 정확한 이산 방정식으로,
  고차 n은 연속 다항식 근사로 처리하고 경계에서 정합성 보장

### 구현 순서 (수치 코어)
1. 단일 구간, 고정 차수 Galerkin 투영으로 순수 성장(propagation)만 있는 PBE 검증
   (해석해 존재: Flory 분포)
2. 정지(결합/불균등화), 사슬이동 텀의 convolution 연산자 구현 및 검증
3. h-refinement: 국소 오차 추정 → 구간 분할/병합
4. p-refinement: 국소 오차 추정 → 다항식 차수 증가/감소
5. discrete-continuous 경계 처리 (저분자량 영역 정합)
6. 다중 분포(공중합체 조성 등 2차원 분포)로 확장 — **가장 어려운 부분**, 후순위

---

## 3. 반응속도론 엔진

- 사용자가 반응 스킴을 선언적으로 기술 (예: `Initiation`, `Propagation`, `ChainTransferToMonomer`,
  `TerminationCombination`, `TerminationDisproportionation`, `Branching`, `Scission`, ...)
- 각 반응 클래스는 "이 반응이 PBE의 생성/소멸 텀에 기여하는 연산자"를 Galerkin 기저로
  표현하는 메서드를 제공해야 함 (`assemble(basis, grid) -> sparse operator`)
- 저분자종(개시제, 모노머, 사슬이동제 등)은 표준 ODE/질량작용 속도식으로 별도 처리,
  PBE와 質량보존으로 연결

**마일스톤**: 자유라디칼중합(FRP) 표준 스킴 하나를 완전히 구현 → 알려진 PREDICI 예제/논문
결과와 MWD, PDI 비교

---

## 4. 시간적분 및 커플링

- 저분자 ODE (수 개 ~ 수십 개 변수) + PBE 계수(구간마다 수~수십 개 계수) → 전체 상태벡터가
  가변 크기 (h-p 적응 때문에 매 스텝 재구성 가능)
- 강건한 적분기 필요: **stiff ODE solver** (BDF, Radau5) 또는 PREDICI처럼
  extrapolation 기반(LIMEX류) 적분기
- Jacobian: 반응 텀이 sparse/구조적이므로 analytic sparse Jacobian 우선 시도,
  안 되면 자동미분(JAX)
- 적응 시간 스텝 + 적응 그리드(h-p)의 상호작용을 관리하는 "outer loop" 설계 필요:
  스텝 실패 시 그리드 재조정 여부 판단 로직

---

## 5. 반응기 모델

- Batch → Semi-batch(공급 스트림) → CSTR(정상상태 + 과도상태) → PFR/cascade 순서로 확장
- 에너지수지(비등온) 는 선택 기능으로 마지막에 추가
- 반응기 모델은 "저분자종 물질수지에 유입/유출/공급 텀을 추가"하는 형태로 PBE 코드와 분리 설계

---

## 6. 후처리 & 검증

- 분포로부터 모멘트(M0, M1, M2) 계산 → Mn, Mw, PDI 산출 및 실시간 플롯
- 전체 MWD (log-normal 스케일) 시각화
- **검증 전략**: (a) 해석해가 있는 단순 케이스(Flory-Schulz, 순수 성장), (b) 모멘트 방정식과
  직접 비교(모멘트법으로 독립적으로 계산 후 PBE 결과의 모멘트와 대조), (c) 가능하면 공개된
  PREDICI 논문 예제의 그래프/수치와 비교
- 파라미터 피팅(선택 기능): 실험 MWD/GPC 데이터에 반응속도상수 최적화 (scipy.optimize 등)

---

## 7. 단계별 로드맵 (마일스톤)

| 단계 | 내용 | 산출물 |
|---|---|---|
| M0 | 수학 정리, 논문 리뷰, 아키텍처 확정 | 설계 문서 |
| M1 | 단일구간 Galerkin + 순수 성장 PBE | Flory 분포 재현 |
| M2 | 정지/이동 반응 텀 + h-refinement | 다양한 termination 모드 검증 |
| M3 | p-refinement + discrete-continuous 결합 | 저분자량 영역 정확도 검증 |
| M4 | 저분자종 ODE 커플링 + 적응 시간적분 | FRP 전체 반응 스킴 batch 시뮬 |
| M5 | Semi-batch/CSTR 반응기 모델 | 산업 예제 재현 |
| M6 | 후처리/시각화/리포트 | MWD·모멘트 대시보드 |
| M7 | (옵션) 공중합체 2차원 분포, 파라미터 피팅, GUI | 확장 기능 |

각 단계는 이전 단계 대비 회귀 테스트를 유지하며 진행해야 합니다 (validation/ 폴더에 계속 축적).

---

## 8. 주요 리스크

- **discrete-continuous 경계 처리**가 논문에서도 가장 까다로운 부분 — 초반에 단순화된
  버전(순수 continuous만)으로 먼저 동작시키고 이후 정교화 권장
- h-p 적응의 오차 추정자 설계가 부정확하면 전체 정확도/안정성에 큰 영향 → 검증 케이스를
  촘촘히 두어야 함
- 가변 크기 상태벡터 + stiff 적분기 조합은 구현 난이도가 높음 — 초기엔 고정 그리드로
  적분기부터 검증 후 적응 로직 추가 권장
- PREDICI의 정확한 내부 알고리즘/파라미터는 상용 소프트웨어라 비공개 세부사항 있음 →
  "동일 원리 기반 재구현"이지 "PREDICI 코드 자체의 복제"는 아님 (라이선스/특허 이슈 회피 위해서도
  독자 구현 필요)

---

## 9. 다음 액션 제안

바로 시작한다면 **M1 (단일구간 Galerkin + 순수 성장)** 부터 코드로 만들어보는 게 좋습니다.
원하시면 이 저장소 스캐폴딩(core/basis.py, core/grid.py 등 뼈대 파일)부터 만들어 드릴게요.
