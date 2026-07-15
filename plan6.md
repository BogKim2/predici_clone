# PREDICI Clone 개발 계획 v6: Full Feature Parity — Monte-Carlo, PSD/Emulsion, Multiphase Thermodynamics, DB, Replay

이 문서는 `plan5.md`(M33~M40, v1.0 릴리스 하드닝)가 **완료된 이후** 진행할 계획이다.
`datas/` 폴더의 **39개 PDF 전체**(Predici 7 매뉴얼, Predici 11 매뉴얼/튜토리얼/워크숍,
버전 릴리스 노트, Parameter Estimation, Monte-Carlo, PSD Tutorial, Emulsion, Cape-Open,
Fugacities, Crosslinking/Condensation 논문 등)를 텍스트 추출 후 병렬 인벤토리 분석하여
**원본 PREDICI/Presto-Kinetics 11의 미구현 기능 전체**를 도출하고, 이를 하나의 완결형
로드맵(M41~M60)으로 묶는다.

전제 조건: `plan5.md`의 Completion Criteria(1~8번)가 모두 충족된 상태(v1.0.0 태그).

## 분석 방법 (Provenance)

- `datas/*.pdf` + 루트 3개 PDF를 `pdftotext -layout`로 추출(총 ~46,000 라인).
- 8개 병렬 에이전트로 주제별 feature 인벤토리 작성:
  1. 현재 구현 인벤토리(`predici_clone/` + plan1~5)
  2. Predici7 Manual(18,900라인, **95개 reaction step**, PDE/PSD, replay, OLE/COM, IDS 등)
  3. Overview/Status/Compendium(아키텍처, 모델 카탈로그)
  4. Monte-Carlo(hybrid SSA, tau-leaping, topology, MC-index, backward coupling)
  5. Parameter Estimation(MDF, reduced-directions SVD, IND, parameter DB)
  6. Polymer chemistry(ATRP/RAFT/NMP, polycondensation, crosslinking, FGD, penultimate)
  7. Reactor/Emulsion/PSD(Smith-Ewart, 구획화 Df, PBE, fugacity/VLE)
  8. Versions/Cape-Open/Tutorials(버전별 changelog, co_* 커맨드, 예제 모델)

---

## 1. 이 단계의 목표

원본 PREDICI 11 / Presto-Kinetics 11의 **미구현 대분류 기능을 모두 구현**한다:

1. **Hybrid Monte-Carlo 엔진** — 현재 스텁뿐. 결정론적 Galerkin 해와 결합된 Gillespie SSA,
   MC-index, tau-leaping, 토폴로지/gyration, sequence length analysis, backward coupling.
2. **Population Balance / PSD(Parsival)** — profile 기반 입자크기분포, nucleation/growth/
   breakage/agglomeration PBE, PDE step family, MSMPR 결정화.
3. **Emulsion polymerization** — 다상 반응기, Smith-Ewart 라디칼 분포, 구획화(Df) 및 rho-c
   모델, 라디칼 entry/exit, 단량체 분배.
4. **다상 반응기 & 열역학** — main/phase1/phase2/own/gas 상, partition reaction,
   solubility 기반 phase exchange, precipitation.
5. **Fugacity / VLE / Cape-Open** — Peng-Robinson EOS, PT flash, `co_action/co_attribute/
   co_get/co_set`, mix density, fugacity coefficient.
6. **Reaction step 라이브러리 확장** — 현재 ~5개 템플릿 → 원본 **95개 패턴** 수준으로 확장.
7. **Controlled radical & step-growth 화학** — ATRP/RAFT/NMP, polycondensation(AA-BB/AA-DD),
   crosslinking/gelation, functional group distribution, penultimate/다단량체 copolymer,
   glass/gel effect.
8. **Parameter DB & parameter/module sets** — 외부 XML DB, `dbpar/dbfunc`, DIPPR, 단위 변환,
   parameter set/module set/group.
9. **Parameter Estimation 완결** — MDF 포맷/에디터, reduced-directions(SVD/상관분석), IND,
   box search, parity/3D residual plot, Arrhenius plot, robust optimization.
10. **Optimal control & Variation tool**, **Replay system**, **Initial Data Sets(IDS/AST)**,
    **Scripting/PID/procedures 완결**, **Interoperability(OLE/COM, Excel, flowsheet, Petri
    chart)**, **GUI 통합**, **워크숍 예제 재현 벤치마크**.

비목표(유지): 원본 파일 포맷(.rsy/.par 등) 바이너리 리버스, PREDICI UI 픽셀 복제,
외부 상용 바이너리(Multiflash 실제 DLL, Wingraphviz.exe) 의존. Cape-Open은 **자체 Python
EOS 및 in-process 어댑터**로 대응하고 실제 COCO/CAPE-OPEN COM 서버 연결은 선택적 어댑터로 남긴다.

---

## 2. Gap 분석 요약

| 도메인 | plan1~5 구현 상태 | plan6 목표 | 마일스톤 |
| --- | --- | --- | --- |
| Reaction step 라이브러리 | ~5 템플릿(propagation/termination/transfer/general) | 95 패턴 계열(초기화·전달·종결·분해·추출·흐름·확산·상·PDE·ODE·bio) | M41 |
| Monte-Carlo 엔진 | STUB(파라메트릭 샘플링 sensitivity만) | hybrid SSA + 결정론 결합, MC-index, 보간, `getmcinfo/getmcaverage` | M42 |
| MC 고급 | 없음 | tau-leaping, topology/gyration, SLA, backward coupling, full-chain, moment-mode MC, ensemble save/reuse | M43 |
| CRP & step-growth 화학 | terminal 2-monomer만 | ATRP/RAFT/NMP, polycondensation, crosslinking/gel, FGD, penultimate, N-monomer, glass/gel effect | M44 |
| PSD / PBE | `particle_size.py` STUB | profile PBE(nucleation/growth/breakage/agglomeration), PSD data, MSMPR | M45 |
| Emulsion | 없음 | 다상 + Smith-Ewart + Df/rho-c + entry/exit + partitioning | M46 |
| 다상 반응기 & phase exchange | 단일상만 | main/phase/own/gas, partition, solubility, precipitation | M47 |
| Fugacity/VLE/Cape-Open | `cape_open.py` STUB | PR-EOS, PT flash, co_* 커맨드, mix density | M48 |
| Parameter DB & sets | 없음 | 외부 XML DB, dbpar/dbfunc, parameter/module set/group | M49 |
| Parameter Estimation | LM/dual-annealing, 다실험 | MDF 포맷/에디터, reduced-directions, IND, box search, parity/3D, Arrhenius plot, robust opt | M50 |
| Optimal control & Variation | shooting(스칼라 1목표)만 | 시간최적/프로파일 최적화, variation tool 그리드 | M51 |
| Replay | 없음 | record/playback, temporary/project replay, MC-from-replay | M52 |
| Initial Data Sets & 분포 생성 | 없음 | IDS/AST 재사용, Schulz-Flory/Poisson/custom 생성기 | M53 |
| Scripting/PID/procedures | 10+ 함수, procedure namespace | PID, 전체 함수(getfeedmass/gettankmass/getphasemass/copyreactor/findroot/getprofmy/co_*), ODE-system step, 디버거 | M54 |
| Heat balance/feed 확장 | UA + coolant | user-defined heat script, cp-derivative, feed temp coupling, variable pressure, mass stream table, feed delay | M55 |
| Interoperability | JSON IO, NPZ, automation API | OLE/COM 서버(Python), Excel export, flowsheet, model 비교/교환, Petri chart | M56 |
| GUI 통합 | 기본 탭 | MC/PSD/emulsion/DB/replay/copolymerization assistant 화면 | M57 |
| 벤치마크 | Flory-Schulz, cascade→PFR, copolymer drift | ATRP/emulsion/gel point/MSMPR/DME fugacity/MC composition/PSD growth | M58 |
| 패키징/문서 | v1.0 | v2.0 | M59~M60 |

---

## 3. Milestone Roadmap

| 단계 | 목표 | 주요 산출물 | 검증 |
| --- | --- | --- | --- |
| M41 | Reaction step 라이브러리 확장(95 패턴 계열) | `kinetics/step_library/*`, 패턴 카탈로그 확장 | 각 패턴 balance 파생 유닛테스트 |
| M42 | Hybrid Monte-Carlo 엔진(core) | `montecarlo/engine.py`, `montecarlo/ensemble.py`, `montecarlo/mc_index.py` | 결정론 대비 CLD/모멘트 수렴 |
| M43 | Monte-Carlo 고급(tau-leaping/topology/SLA/backward) | `montecarlo/tau_leap.py`, `montecarlo/topology.py`, `montecarlo/sequence.py` | 분석해/결정론 대비 벤치마크 |
| M44 | CRP & step-growth 화학 확장 | `kinetics/mechanisms/{atrp,raft,nmp,polycondensation,crosslink}.py`, `kinetics/fgd.py` | ATRP MWD, gel point, 조성 벤치마크 |
| M45 | PSD / Population Balance(Parsival) | `psd/pbe.py`, `psd/kernels.py`, `psd/profile.py`, PDE step 모듈 | MSMPR 해석해, 성장/핵생성 벤치마크 |
| M46 | Emulsion polymerization | `emulsion/smith_ewart.py`, `emulsion/compartment.py`, `emulsion/rho_c.py` | Smith-Ewart 극한, Df 극한 케이스 |
| M47 | 다상 반응기 & phase exchange | `reactor/phases.py`, `kinetics/phase_steps.py` | 상 부피/질량 수지, partition 평형 |
| M48 | Fugacity / VLE / Cape-Open | `thermo/peng_robinson.py`, `thermo/flash.py`, `api/cape_open.py` 실구현, `script/cape_commands.py` | DME fugacity 재현, PT flash 수렴 |
| M49 | Parameter DB & parameter/module sets | `db/parameter_db.py`, `api/parameter_sets.py`, `api/module_sets.py`, `script/db_commands.py` | dbpar/dbfunc, set 전환 계약 테스트 |
| M50 | Parameter Estimation 완결 | `fitting/mdf.py`, `fitting/reduced_directions.py`, `fitting/ind.py`, `fitting/box_search.py`, `fitting/arrhenius.py` | reduced-DOF/조건수, parity, Arrhenius fit |
| M51 | Optimal control & Variation tool | `optimize/optimal_control.py`, `optimize/variation.py` | 시간최적/프로파일 최적화 목표 도달 |
| M52 | Replay system | `engine/replay.py`, replay 오버뷰 GUI | 재생 결과=원 시뮬 동등성 |
| M53 | Initial Data Sets & Distribution Generator | `api/initial_data.py`, `postprocess/dist_generator.py` | IDS 재사용, Schulz-Flory/Poisson 정확도 |
| M54 | Scripting/PID/procedures 완결 | `script/function_catalog.py` 확장, `control/pid.py`, `script/ode_system.py`, 디버거 | 전체 함수 계약, PID 정정 거동 |
| M55 | Heat balance/feed 확장 | `reactor/energy_balance.py` 확장, `reactor/feed.py`, `reactor/pressure.py` | user heat script=내장식 일치, cp-derivative |
| M56 | Interoperability(OLE/COM, Excel, flowsheet, Petri) | `api/automation_server.py`, `interop/excel_export.py`, `interop/flowsheet.py`, `interop/reaction_graph.py` | 자동화 서버 계약, Petri 그래프 렌더 |
| M57 | GUI 통합(신규 서브시스템) | MC/PSD/Emulsion/DB/Replay 탭, copolymerization assistant | offscreen 스모크, 워크플로 테스트 |
| M58 | 워크숍 예제 재현 벤치마크 | `validation/benchmarks/*`(ATRP/emulsion/gel/MSMPR/DME/MC) | 각 벤치마크 허용오차 통과 |
| M58b | **`test_manuals/` 통합 실행 프로그램** — 39개 매뉴얼의 모든 기능을 실행/재현하는 러너 | `test_manuals/`(예제·러너·CLI·리포트) | `python -m test_manuals --all` 전 예제 실행·리포트 생성 |
| M59 | Packaging & Docs v2.0 | PyInstaller 재빌드, 매뉴얼 신규 챕터 | clean-venv 빌드+스모크 |
| M60 | v2.0 Regression Freeze | 전체 스위트/매뉴얼/스모크 통합 | `pytest -q` 전체 통과, `v2.0.0` 태그 |

---

## 4. Detailed Implementation Plan

### M41. Reaction Step Library Expansion

#### Scope
현재 `kinetics/templates.py`의 소수 템플릿을 Predici7 매뉴얼 5장의 **95개 reaction step** 계열로
확장한다. 각 스텝은 (a) 종/분포에 대한 stoichiometry, (b) rate law, (c) Galerkin operator로의
변환 규칙을 갖는 선언형 데이터로 표현한다.

#### Requirements
- `kinetics/step_library/` 하위에 카테고리별 스텝 정의:
  - **초기화**: Initiation, Radical initiation, Initiator decay, Polyfunctional initiation,
    Initiation in polymer phase, Initiation of n-mer.
  - **성장**: Propagation, Propagation(copolymer), Propagation(copolymer, r-value),
    Propagation in polymer phase, Propagation of n-mer, **k(s)-Propagation**(사슬길이 의존).
  - **전달**: Transfer(monomer/solvent/agent), Transfer(copolymer), **Transfer to polymer(LCB)**,
    H-transfer with scission, Cross transfer with scission, Transfer with counter species.
  - **종결**: Combination, Disproportionation, Combi/Dispro, (s,r) 변형, copolymer 변형,
    Double termination, **k(s)-Termination**, LCB termination.
  - **분해**: Degradation at chain end(±termination), Degradation of n-mer, Degradation(s,r),
    Degradation(statistical), Degradation(weighted), Combi-Scission.
  - **추출/흐름/수송**: Extraction/Extraction2(±n-mer), Flow(high/low-mol), Convection(high/low),
    Diffusion(high/low), Masstransfer, Reactor transfer, Collected flow(high/low/direct).
  - **상**: Gelation, PhaseExchange, Phasetransfer, Precipitation, Change of characteristic,
    Balance steps, Comment.
  - **일반/시스템**: Elemental(±efficiency/n-th/user-order), Equilibrium, Reversible,
    General kinetic step, Stoichiometry, (General) ODE-systems, Bio kinetics.
  - **PDE 계열**(M45에서 완성): PDE:Kinetic/EKinetic/Agglomeration(±L)/Breakage/Convection(±2)/
    Diffusion(±2)/Nucleation/Reaction(±2/3)/ReactionBC/Flux/Fluidbalance/Feed-Profile/Recycle/
    Transition/Dirichlet(-left/-right)/Neumann(±2)(-left/-right).
- 각 스텝은 `is_polymer`/`is_pde`/`is_phase` 카테고리 태그와 PatternFinder 필터 키워드를 갖는다.
- rate law: mass-action, power-law, Arrhenius(k0/E-R/DV-R, ref-temp/ref-reactor), r-value,
  `k(File)`/`k*File` 스크립트 오버라이드(이미 존재하는 `reaction_modifiers.py` 재사용).
- 기존 FRPScheme/GeneralKinetic 경로가 새 라이브러리로 리팩터링되되 **회귀 없음**.

#### Acceptance Criteria
- 각 (비 PDE) 스텝에 대해 단일 스텝 모델의 balance ODE가 해석적 기대와 일치.
- PatternFinder에서 카테고리/키워드로 95개 계열이 필터링된다.
- 기존 M8~M40 회귀 테스트 전부 통과.

#### Tests
- `tests/test_step_library.py`(스텝별 balance 파라미터화 테스트), PatternFinder 확장 테스트.

---

### M42. Hybrid Monte-Carlo Engine (Core)

#### Scope
Monte-Carlo 스텁을 실제 엔진으로 대체한다. `Schuette-Wulkow_Predici-MonteCarlo.pdf` /
`Predici11_Hybrid-Monte-Carlo.pdf` / 워크숍 5의 hybrid 결정론-확률 결합을 구현한다.

#### Requirements
- `montecarlo/ensemble.py`: 분포별 chain ensemble `E_i`(사슬길이 s + property index 벡터 저장),
  ensemble 크기(기본 100, 종별 조정), control volume V(결정론 농도 ↔ ensemble 밀도 매칭).
- `montecarlo/mc_index.py`: 반응 스텝에 부여하는 추상 property index(단량체 카운트, 분기 카운트,
  crosslink 카운트 등, alias 명명), 스텝별 증분 규칙.
- `montecarlo/engine.py`:
  - 결정론 적분기(기존 `integrator/stepper.py`)가 만든 시간 스텝 `Δt`마다 `n_MC`개의 Gillespie
    substep 실행(Δt_k = (1/r_T)·ln(1/z_k), Σ Δt_k < Δt).
  - 총 반응율 `r_T = Σ r_m`, 반응 선택은 [0,1] 구간분할, unimolecular/bimolecular 처리.
  - 사슬 선택: unimolecular 랜덤, bimolecular 두 ensemble에서 선택(m_a 가중/복제),
    사슬길이 가중 선택(transfer-to-polymer용, 누적 길이 기반).
  - t=0 시딩: 결정론 h-p 분포 `P_i(s)`에서 ensemble 초기화, property index 0/랜덤.
- `montecarlo/interpolation.py`: h-p 격자 구간별 property 평균 → 구간 중점 배정 → 선형 보간으로
  매끈한 chain-length-dependent 곡선 생성.
- 스크립트 커맨드: `getmcinfo(name, type)`(0~13 타입: 0-2 모멘트, 3-4 평균 사슬길이/무게,
  5-10 MC-index 평균, 11-12 오차, 13 분기수), `getmcaverage(name, s, index, interpolated)`.
- 지원 스텝(초기 범위): initiation, propagation, transfer to small molecule, recombination,
  disproportionation, transfer to polymer/LCB, cross-linking.
- MC 활성화 토글 및 스텝별 MC-index 지정 UI 스키마(GUI는 M57).

#### Acceptance Criteria
- 단순 FRP에서 MC-평활 CLD가 결정론 Galerkin CLD와 지정 오차(2~6%, ensemble 100~5000) 이내로 일치.
- `getmcinfo`의 M_n/M_w가 결정론 모멘트와 일치.
- 오차가 O(1/√m)로 감소함을 수치적으로 확인.

#### Tests
- `tests/test_mc_engine.py`, `tests/test_mc_interpolation.py`, `tests/test_mc_script_commands.py`.
- 벤치마크 `validation/benchmarks/mc_vs_deterministic_cld.py`(다중 realization + 오차 회귀).

---

### M43. Monte-Carlo Advanced

#### Scope
성능·정확도·구조정보 확장. `Predici_Maxwell.pdf`의 통합 iteration 및 버전 노트(11.13.3/14.3/16.1)의
MC 기능을 반영한다.

#### Requirements
- `montecarlo/tau_leap.py`: 빠른 propagation 반응 번들링(n_fast·τ_fast ≈ τ_slow), 결정론 상한 +
  정확도 제약, 공중합에서 propagation 속도차 큰 경우 이득.
- `montecarlo/topology.py`: 분기 리스트(branch length/connection point/type), transfer-to-polymer/
  cross-link 시 토폴로지 갱신, β-scission 재구성, freely-jointed/freely-rotating random walk로
  gyration 반경 R_g 및 shrinking factor g 계산, gyration radius export(WriteMCDist).
- `montecarlo/sequence.py`: Sequence Length Analysis 2모드 —
  (a) full-chain 모드(전체 이벤트 리스트, 블록 길이),
  (b) automatic sequencing(전체 사슬 저장 없이 sequence 시작/중지/결합 추적, 저비용·고속).
- `montecarlo/backward_coupling.py`: MC로 계산한 chain-length-dependent property를 결정론 rate에
  피드백(transfer-to-polymer branching 확률 등), 결정론 counter와의 일관성 체크.
- moment-mode MC(결정론 분포는 moment 방정식, MC는 property만), MC branch-on-backbone(grafting),
  Transfer(LCB)/s-Termination/Degradation/Double termination의 MC 준비 옵션.
- MC ensemble 저장/재사용/이전 실행으로부터 초기화(bimodal 예시), full-chain 모드(선택, 메모리 경고).

#### Acceptance Criteria
- tau-leaping이 정확도 저하 허용 범위 내에서 MC 부분 10~100× 가속.
- gyration/shrinking factor g가 하이퍼브랜치 참고값(≈0.6~0.65) 근방.
- automatic SLA가 full-chain SLA와 정규화 분포에서 일치하되 유의미하게 빠름.
- backward coupling on/off가 PDI/branch 분포에 물리적으로 타당한 차이를 낸다.

#### Tests
- `tests/test_tau_leap.py`, `tests/test_mc_topology.py`, `tests/test_sequence_length.py`,
  `tests/test_backward_coupling.py`.

---

### M44. Controlled Radical & Step-Growth Chemistry

#### Scope
`Predici11 Polymer Tutorial`, 워크숍 3/4, `CrossLinkingModels`, `New Condensation Flags`,
`Polycondensation of AA_DD`, `Hutchinson ... Functional group distribution`, `Fu ATRP`,
`exercise_atrp`를 반영해 화학 메커니즘을 확장한다.

#### Requirements
- `kinetics/mechanisms/atrp.py`: 활성/비활성 평형(dormant X-Pn ↔ Pn·), persistent radical effect,
  Cu(I)/Cu(II) redox, 촉매 solubility(precipitation 스텝 연동), initiator efficiency `fATRP`.
- `kinetics/mechanisms/raft.py`, `kinetics/mechanisms/nmp.py`: 가역 전달/fragmentation, nitroxide
  활성/비활성 평형.
- `kinetics/mechanisms/polycondensation.py`: AA-BB / AA-DD 다관능 end-group 분류(PsXY 종),
  선택적 반응성(A↔B/C/D만), stoichiometric factorial, Schulz-Flory 예측(등몰).
- `kinetics/mechanisms/crosslink.py`: cross-linker(DVB 등), 네트워크 종(RN/PN), gel point 검출
  (cn = (np−nc)/max(1,np−nc)), gel fraction fnet, 두 접근(generation/fractionation, gelation step).
- `kinetics/fgd.py`: Functional Group Distribution — counters 모델(D0/D1/D 확장 종) + MC full-chain
  추적, subdistribution(0/1/2/3+ functional unit) 출력.
- Copolymer 확장: **penultimate model**(P11/P12/P21/P22, triad counter Cijk),
  **N-monomer(>2)** terminal model, r-value/직접계수 입력(Copolymerization assistant와 정합).
- Glass/gel effect: `getx`/viscosity 스크립트 기반 kp/kt 수정(튜토리얼 1의 etar 모델), procedure
  체이닝(UCOMP/ETA_COMP/KT_COMP/KP_COMP).
- Change-of-characteristic, thermal initiation(styrene Diels-Alder) 지원.

#### Acceptance Criteria
- ATRP 배치가 좁은 MWD(낮은 PDI)와 선형 Mn-전환율 관계를 재현.
- Polycondensation 등몰 recipe가 Schulz-Flory 분포/PDI≈2로 수렴.
- Crosslinking 모델이 임계 전환율에서 gel point 검출(cn→1) 및 gel fraction 증가.
- FGD counters 모델과 MC full-chain 모델의 subdistribution이 상호 일치.
- 단일 단량체/terminal 축약이 M37 기존 결과와 회귀 없이 일치.

#### Tests
- `tests/test_atrp.py`, `tests/test_polycondensation.py`, `tests/test_crosslink_gel.py`,
  `tests/test_fgd.py`, `tests/test_penultimate.py`.
- 벤치마크 `validation/benchmarks/atrp_mwd.py`, `validation/benchmarks/gel_point.py`.

---

### M45. Population Balance / PSD (Parsival)

#### Scope
`PrediciPSD_Tutorial_2017.pdf`를 주 소스로 profile 기반 입자크기분포(PSD)와 결정화 PBE를 구현한다.
`postprocess/particle_size.py` 스텁을 대체한다.

#### Requirements
- `psd/profile.py`: profile(연속 좌표 L 위 분포), 격자(min/max, linear/log), number density n(L),
  volume density n3(L), shape factor kv(구 π/6), 모멘트 μk = ∫ Lk n(L) dL, 평균크기 L̄=μ1/μ0,
  총부피 Vc=kv·μ3.
- `psd/pbe.py`: Population Balance ∂(V·n)/∂t + ∂(G·n)/∂L + 부피변화항 = birth − death + in − out,
  method-of-lines 공간이산화 후 기존 적분기 재사용.
- `psd/kernels.py`:
  - **Growth** G(L)=kg·(c−csat)^g(크기 독립/의존), solute 질량보존 자동결합.
  - **Nucleation** b(L)=f(L)·bnucl(primary/secondary, f(L) 정규화 nucleus 형상).
  - **Breakage** d_break(L) + 이항분열 birth(부피보존, daughter 분포 P(L,L')).
  - **Agglomeration** α(v,w) kernel(부피좌표 자연, L좌표 Jacobian 변환).
- PDE step family(M41에서 선언, 여기서 수치 구현): PSD:Growth1, PSD:Nucleation, PDE:AgglomerationL,
  Breakage, Feed-Profile, Convection/Diffusion, ReactionBC, Dirichlet/Neumann BC.
- `psd/psd_data.py`: PSDData `abcd` 포맷(정규화/가중/스케일/절대상대) 임포트, distribution generator
  (Gaussian/log-normal/uniform, 슬라이더 파라미터).
- 스크립트: `getprofmy(name, k)` 모멘트, profile 적분(부피/질량), boundary condition(Lmin 소멸).
- MSMPR 연속 결정화기(inlet/outlet, 체류시간 τ=V/F, steady-state), 오차 가중(mass 1.5/volume 1.2/
  number 1.0).
- 결합 모델: 반응기 kinetics(moment mode) + PSD full 분포, size-dependent 라디칼 분포 f_n(x)
  (n 라디칼 보유 입자, M46 emulsion과 공유).

#### Acceptance Criteria
- 크기독립 성장 only의 MSMPR가 해석적 평균크기/모멘트와 일치.
- 핵생성+성장 배치에서 질량보존(solute + crystal)이 지정 허용오차 내 유지.
- Agglomeration이 μ0 감소·μ3 보존을 만족.
- 격자 자동 확장(입자가 Lmax 초과 시)이 동작.

#### Tests
- `tests/test_psd_pbe.py`, `tests/test_psd_kernels.py`, `tests/test_msmpr.py`.
- 벤치마크 `validation/benchmarks/msmpr_analytic.py`, `validation/benchmarks/psd_growth_mass.py`.

---

### M46. Emulsion Polymerization

#### Scope
`Wulkow - Emulsion - Workshop`, 워크숍 6, `Predici11_Workshop ... Emulsion`을 반영해 구획화
에멀전 중합을 구현한다. M45(PSD)와 M47(다상)에 의존.

#### Requirements
- `emulsion/smith_ewart.py`: 라디칼 수 분포 N(n) 3항 방정식(entry ρ, exit kd, termination c),
  PREDICI의 profile(사슬길이 index=n) 표현 + moment shift(μ1(N)=μ1'−μ0 등), k(s)-propagation/
  k(s)-termination로 구현.
- `emulsion/compartment.py`: 구획화 계수 Df = [μ2(N)−μ1(N)]/[(μ1/μ0)²], 극한(0-1-2 vs pseudo-bulk),
  종결율 승수 적용.
- `emulsion/rho_c.py`: rho-c 모델(ρ-chain/c-chain 분류, initiation 분기 fraction=N(0)/μ0,
  Dfcc/Dfrhoc 별도 종결율).
- `emulsion/entry_exit.py`: aqueous-phase 올리고머(Rw1..Rw4) entry(critical chain length scrit),
  exit/disproportionation, phase-transfer 스텝(IsO→IsP).
- `emulsion/partition.py`: 단량체 3상 분배(water/polymer/droplet), Kwp/Kdp partition coefficient,
  kla 완화, solubility 기반 phase exchange.
- 입자 nucleation(micellar/secondary), 입자수 tracking(상수 가정 또는 동적 N(t)), 에멀전 공중합
  (조성 counter, penultimate 지원), 에멀전 crosslinking(RN/PN, fnet).

#### Acceptance Criteria
- Combination termination 비활성 시 Smith-Ewart N(n)이 해석적 정상상태와 일치.
- Df가 0-1-2 극한(≪1)과 pseudo-bulk 극한(≈1)을 재현.
- rho-c 모델이 표준 pseudo-bulk 대비 물리적으로 타당한 MWD/조성 차이를 낸다.

#### Tests
- `tests/test_smith_ewart.py`, `tests/test_compartmentalization.py`, `tests/test_rho_c.py`,
  `tests/test_monomer_partition.py`.
- 벤치마크 `validation/benchmarks/emulsion_df_limits.py`.

---

### M47. Multiphase Reactor & Phase Exchange

#### Scope
`Feed and heat balance v2` + 워크숍 예제(PartitionReaction/PhasesWater/PhasesSteps)를 반영해
반응기 상(phase) 구조를 도입한다.

#### Requirements
- `reactor/phases.py`: main phase + 최대 2개 reactive phase + own phase(단량체 droplet) + gas phase,
  자동 부피수지 V = Vmain + Vphase1 + Vphase2 + Vown, 상별 반응/부피 배정.
- `kinetics/phase_steps.py`: PhaseExchange(대수 partition 방정식), Phasetransfer(kinetics),
  Precipitation(phase equilibrium), solubility(Henry 유형) 기반 분배, 직접 전달.
- DAE 통합: 미분(농도/폴리머/온도/PSD) + 대수(상평형/flash/부피·밀도 제약), 시작 시 consistency
  projection(기존 `integrator` 확장).
- density-dependent 상평형(Asua 공중합 모델의 11변수 대수계 예시 지원).

#### Acceptance Criteria
- 상별 질량/부피 수지가 전역 보존.
- partition 스텝이 지정 평형(Kwp 등)으로 수렴.
- 단일상 축약이 기존 반응기 결과와 회귀 없이 일치.

#### Tests
- `tests/test_phases.py`, `tests/test_phase_exchange.py`.

---

### M48. Fugacity / VLE / Cape-Open

#### Scope
`Fugacities in Predici and Presto Kinetics`, `Predici11_Cape-Open`, 버전 16.1의 mix density,
워크숍 예제(DME_Fugacities)를 반영. `api/cape_open.py` 스텁을 실구현으로 대체.

#### Requirements
- `thermo/peng_robinson.py`: PR-EOS(A/B from Tc/pc/acentric factor), 압축인자 Z를 `findroot`
  (Newton, tol 1e-6)로 해, per-compound log fugacity coefficient 스크립트(H2/CH3OH/DME/CO2/N2/Ar 등).
- `thermo/flash.py`: PT flash(상분리, phase split, component distribution, mix property), 시간
  스텝 시작마다 자동 실행 + 결과 캐시.
- `thermo/property_package.py`: compound/EOS/flash type/요청 property를 담는 설정(.xml), Cape-Open
  configurator(생성/편집/삭제/프로젝트 반영), 실제 COCO/CAPE-OPEN COM 연결은 선택적 어댑터.
- `script/cape_commands.py`: `co_action("PT")`, `co_attribute(compound, prop, T)`,
  `co_get(info, phase, compound)`, `co_set(info, phase, compound, value)`; 4-커맨드 진행바/오류
  색상(녹/적/황/백) 상태 노출.
- mix density(RhoMix 스크립트, 비이상 혼합물), 부피변화 추적(RhoDirect vs EOS density), fugacity/
  log-fugacity coefficient 확장, gas-phase pressure control.

#### Acceptance Criteria
- DME/fugacity 예제가 참조 결과와 지정오차 내 일치.
- PT flash가 알려진 이원계에서 phase split을 정확히 예측.
- mix density 사용 시 부피변화가 물리적으로 타당(constant density 대비 관측 가능).

#### Tests
- `tests/test_peng_robinson.py`, `tests/test_flash.py`, `tests/test_cape_commands.py`.
- 벤치마크 `validation/benchmarks/dme_fugacity.py`.

---

### M49. Parameter Database & Parameter/Module Sets

#### Scope
`Version_11_15_1_Parameter_Sets and DB.pdf`를 반영해 파라미터 데이터베이스와 set/group 관리를 구현.

#### Requirements
- `db/parameter_db.py`: 외부 XML DB, "Sets"(substance/reaction/general), Parameters(MW/TC/PC/ACEN,
  DIPPR 속성), Functions(온도/압력 의존 다항식/USER 수식, range/error/source/rating), 단위 시스템
  (자동 변환 + custom 단위), clipboard import(Set/Name/Desc/Value/Unit), Excel export(set별 sheet).
- `script/db_commands.py`: `dbpar("Set","Property",[Unit])`, `dbfunc("Set","Property",T,[Unit])`,
  USER 함수(변수 T/P/A~E 대문자).
- 모델 연동: species에 MW/density/heat capacity 함수 배정, parameter에 "use DB" 체크(값 덮어쓰기,
  Arrhenius part별 override), project database(자체완결 백업, read-only, "Save copy as"로 외부화).
- `api/parameter_sets.py`: named parameter set(값만 상이, 동일 character/ref-temp/reactor 제약),
  duplicate/synopsis/activate/diff, 상속 규칙(신규 파라미터 default, override 전파).
- `api/module_sets.py`: reaction module set(활성상태만 상이), group 기반 토글, group에서 module set
  생성, combined parameter+module set(자동 연동).
- 확장 group 관리: 다중 group 배정(CTRL+drag), group rename, group→module set.

#### Acceptance Criteria
- `dbpar`/`dbfunc`가 단위 변환 포함해 정확한 값을 반환.
- parameter set 전환이 값만 바꾸고 구조는 유지(제약 위반 시 거부).
- module set 전환이 반응 스텝 활성만 바꾼다.

#### Tests
- `tests/test_parameter_db.py`, `tests/test_parameter_sets.py`, `tests/test_module_sets.py`.

---

### M50. Parameter Estimation Completion

#### Scope
`CiT/Predici/Presto Parameter Estimation` + 워크숍 2를 반영해 M35의 fitting을 원본 수준으로 완결.

#### Requirements
- `fitting/mdf.py`: MDF(Measured Data File) 포맷(STRUCTURE/END_Data/End, `times` 열, `Func:`/`Proc:`
  접두, scale/weight 행, 초기조건 zero line은 최신 스펙대로 recipe 기반으로 대체), MDF 에디터
  스키마(keyword 검증, 통계 min/max/σ², thin-out/highlight), `coeff:param`/`press_start` 키워드,
  다중 MDF 동시 fitting, recipe 연결.
- `fitting/reduced_directions.py`: Jacobian SVD(J=USVᵀ), condition threshold(기본 100), essential
  DOF 식별, projector 기반 약민감 방향 제거, 원 파라미터 공간 재변환, correlation matrix,
  singular value 리스트, s1/sn 조건비.
- `fitting/ind.py`: Internal Numerical Differentiation — 초기 적분의 적응 시간격자 캐시 후 비적응
  섭동, 정확도 ~√(machine ε), 섭동범위 Δp≈tol.
- `fitting/box_search.py`: 그리드 스캔(하/상한, grid point 수, linear/log, 추가노드), global 초기화.
- `fitting/arrhenius.py`: 다온도 등온 fit 후 Arrhenius plot(ln k vs 1/T 또는 1/(T−Tref)) 선형회귀,
  text export.
- robust optimization(2단계: PE→sensitivity→불확실성 하 최적화, sigma-point 이용), objective
  (스칼라/MFI/조성/full MWD/GPC, f2(T)=Σ((Psim−Pmes)²/Pmes²)), 상대 스케일링+cut-off, per-column
  weight/activation, missing value(−) 처리.
- 분석: "Analyze MDFs"(실험별 residual 기여, 시간구간 편차), "Analyze Parameters"(iteration별 진화),
  parity plot(전 MDF 결합), 3D OpenGL box-search residual(축 파라미터 선택), reset-to-model-values.

#### Acceptance Criteria
- 상관 있는 파라미터쌍에서 reduced-directions가 essential DOF 수를 정확히 보고(예: 4파라미터 3독립).
- IND on/off가 자코비안 정확도/수렴에 기대대로 영향.
- Arrhenius plot이 합성 다온도 데이터에서 원 k0/Ea를 복원.
- synthetic recovery(M35) 회귀 유지.

#### Tests
- `tests/test_mdf.py`, `tests/test_reduced_directions.py`, `tests/test_ind.py`,
  `tests/test_box_search.py`, `tests/test_arrhenius_plot.py`.

---

### M51. Optimal Control & Variation Tool

#### Scope
Predici7 매뉴얼 15/16장 + Overview의 최적제어/robust optimization을 구현.

#### Requirements
- `optimize/optimal_control.py`: 목적(전환율/Mn/viscosity/조성/MWD/시간최적), 조작변수(온도 프로파일,
  feed 프로파일, startup, feed delay, 반응시간), 알고리즘(dual-annealing/직접법), integral 목적함수
  f1(T)=∫(M*n−Mn)²dt, 다목적 가중결합, safety 제약.
- `optimize/variation.py`: parameter variation tool(범위/스텝, 순차 시뮬, break/resume, 결과 survey,
  변형 서브디렉토리), 3D box 시각화 연동.

#### Acceptance Criteria
- 시간최적 제어가 단순 목표(목표 전환율에서 배치시간 최소)에 수렴.
- feed/온도 프로파일 최적화가 목표 product property로 수렴.
- variation tool이 그리드 전 조합을 실행·집계.

#### Tests
- `tests/test_optimal_control.py`, `tests/test_variation.py`.

---

### M52. Replay System

#### Scope
버전 11.13.3의 replay 기능을 구현.

#### Requirements
- `engine/replay.py`: "Create replay"(전체 시뮬 단계 저장: 파라미터/상태변수/폴리머 분포/공간
  profile/선택적 MC), temporary replay(시뮬 중) → project replay(종료 시 승격), replay 오버뷰
  (저장 시간스텝 리스트, 더블클릭 이동), 재계산 없는 고속 재생, replay validity check(종/변수 존재).
- replay로부터 user-defined output 재평가/확장, MC topology를 임의 replay 시각에서 조회, full-chain
  모드 replay(메모리 경고), "Save replay in project file"/"Include MC all results" 토글.

#### Acceptance Criteria
- 재생 결과가 원 시뮬레이션 출력과 수치적으로 동등.
- replay에서 새 output 함수 추가 시 재시뮬 없이 평가된다.
- MC 중간시각 결과 조회가 동작.

#### Tests
- `tests/test_replay.py`, `tests/test_replay_output.py`.

---

### M53. Initial Data Sets (IDS/AST) & Distribution Generator

#### Scope
Predici7 9~10장 + 버전 16.1 distribution generator를 구현.

#### Requirements
- `api/initial_data.py`: 이전 시뮬 출력을 초기조건으로 로드(IDS), assignment table(AST)로 로드 데이터↔
  신규 모델 컴포넌트 매핑, 복수 IDS 결합(예: tubular→CSTR cascade), h-p 분포 초기화.
- `postprocess/dist_generator.py`: Schulz-Flory(mean 지정)/Poisson/custom 함수 스크립트, discrete/
  continuous 모드, 슬라이더 파라미터(임시 조정)→accept, min/max popup, GPC 에디터로 내보내기,
  recipe에 초기 폴리머 분포 배정(absolute mass 권장).

#### Acceptance Criteria
- IDS 재사용으로 한 반응기 출력이 다음 모델 초기조건이 된다.
- Schulz-Flory/Poisson 생성 분포의 Mn/Mw가 지정 파라미터와 일치.

#### Tests
- `tests/test_initial_data.py`, `tests/test_dist_generator.py`.

---

### M54. Scripting / PID / Procedures Completion

#### Scope
Predici7 12~13장 + 버전 노트의 스크립트 커맨드를 완결.

#### Requirements
- `control/pid.py`: PID 컨트롤러(P/I/D, setpoint, measured/control), `pid("name")` 스크립트,
  recipe 동적 조정 연동.
- `script/function_catalog.py` 확장: 기존 10+에 더해 `getmn/getmw/getmz`, `getmolpart/getmasspart`,
  `getfeedmass/getfeedmol/gettankmass/gettankmol`, `getphasemass`, `getdensity/getmass/getpressure/
  gettemp`, `copyreactor(src,dst,factor)`, `findroot`, `getprofmy`, `getmcinfo/getmcaverage`,
  `co_action/co_attribute/co_get/co_set`, `dbpar/dbfunc`, `WriteMCDist`.
- `script/ode_system.py`: (General) ODE-system 스텝(kinetics와 직교하는 사용자 미분방정식),
  equation library(대수/미분), output variable library.
- reactor cascade via script: `copyreactor` + Schedule 스크립트(스테이지 전환, 탱크 재충전, flow
  index로 MC 이력 추적), CollectedFlow_direct feed control.
- 스크립트 디버거: line-by-line 실행, 중간값 검사, breakpoint, 시뮬 중 디버그, procedure 체이닝
  (WinGraphviz 없이 자체 그래프), template library.

#### Acceptance Criteria
- PID가 setpoint 편차를 정정하는 폐루프 거동을 낸다.
- 확장 함수 전체가 계약(반환값/단위) 테스트 통과.
- `copyreactor`+Schedule로 명시적 flow 스텝 없이 cascade가 재현된다.

#### Tests
- `tests/test_pid.py`, `tests/test_function_catalog_full.py`, `tests/test_ode_system.py`,
  `tests/test_copyreactor_cascade.py`.

---

### M55. Heat Balance / Feed Extensions

#### Scope
`Feed and heat balance v2.pdf` + 버전 노트(11.14.x)를 반영해 M34 energy balance를 확장.

#### Requirements
- `reactor/energy_balance.py` 확장: user-defined heat balance script("Reaction heat ~ function",
  dT/dt=result1), cp-derivative treatment(d(cp)/dt 포함, 다성분 feed), 검증모드(스크립트로 내장식
  재현), reaction step별 enthalpy 직접입력(condensation 포함), Arrhenius kp(T) 열원.
- `reactor/feed.py`: mass stream table(linear/step 보간), feed temperature(constant/table/script,
  switch time), feed delay(테스트 기능), 다상 동시 feed, 별도 volumetric vs mass flow.
- `reactor/pressure.py`: variable pressure(script/table, t=0 평가), gas-phase pressure control,
  pressure-dependent kinetics(DV/R term).

#### Acceptance Criteria
- user-defined heat script가 내장 heat balance와 수치적으로 일치(검증모드).
- cp-derivative on일 때 다성분 feed 온도거동이 물리적으로 타당.
- feed temperature/switch time이 스케줄대로 반영.

#### Tests
- `tests/test_user_heat_balance.py`, `tests/test_feed_extensions.py`, `tests/test_pressure.py`.

---

### M56. Interoperability (OLE/COM, Excel, Flowsheet, Petri)

#### Scope
Predici7 31~32장 + 버전 노트의 상호운용 기능을 구현(외부 상용 바이너리 없이).

#### Requirements
- `api/automation_server.py`: OLE/COM 자동화 서버에 대응하는 **Python in-process automation API**
  (50+ 커맨드 상당: 모델 로드/실행/결과조회/파라미터 설정, `ActivateDetailedIteration`,
  `ActivateQBasicIteration`(heat balance shooting), `WriteMCDist`), 선택적 실제 COM 래퍼는 어댑터로.
- `interop/excel_export.py`: 차트(단일/선택/탭/전체) → workbook(sheet 분리/개별), project workshop
  리스트, parameter estimation 결과(parity/single MDF) export(openpyxl).
- `interop/flowsheet.py`: flowsheet 모듈(레이아웃, 컴포넌트/반응기 정보, export/print).
- `interop/reaction_graph.py`: 반응 네트워크 Petri chart(networkx + graphviz 파이썬 바인딩, 외부
  exe 불필요), model 비교/객체 교환(프로젝트 간 drag/diff), HTML/archive export.

#### Acceptance Criteria
- 자동화 API만으로 튜토리얼 프로젝트를 처음부터 끝까지 재현(기존 M38 확장).
- Excel export가 차트/리스트/PE 결과를 올바른 sheet 구조로 생성.
- Petri chart가 반응 스킴 그래프를 렌더(외부 바이너리 없이).

#### Tests
- `tests/test_automation_server.py`, `tests/test_excel_export.py`, `tests/test_reaction_graph.py`.

---

### M57. GUI Integration for New Subsystems

#### Scope
M42~M56 백엔드를 M33 GUI 현대화 패턴(비모달 인스펙터, 공용 위젯) 위에 통합.

#### Requirements
- **Monte-Carlo 탭**: MC 활성화 토글, 종별 ensemble 크기, 스텝별 MC-index 지정, tau-leaping 옵션,
  topology/gyration 뷰, sequence length 출력, MC vs 결정론 비교 차트, full-chain 시각화(포인트 선택).
- **PSD 탭**: profile 격자/PSD data 임포트, distribution generator(슬라이더), PDE step 배정, PSD
  모멘트/평균 출력, MSMPR 설정.
- **Emulsion**: 다상 recipe(상별 색상), Smith-Ewart/rho-c 설정, partition coefficient.
- **Parameter DB**: DB 브라우저(set/parameter/function), "use DB" 체크, parameter/module set/group
  관리, synopsis/diff.
- **Replay 오버뷰**: 시간스텝 리스트, 이동, MC-from-replay.
- **Copolymerization assistant**: 단량체 수, 스텝 활성(INIT/PROP/TRANSFER/TERM), ULTIMATE/penultimate,
  cross-propagation(직접계수/r-value), 자동 모델 생성.
- Reference results(버전 16.1): drag&drop reference 로드, 차트 오버레이(주황 점선, M33 토큰 재사용),
  project 비교.

#### Acceptance Criteria
- 각 신규 탭이 모달 깊이 2단 이하(M33 계약)로 편집 완료.
- 백엔드 기능이 GUI에서 end-to-end 실행된다(offscreen).

#### Tests
- `tests/test_gui_mc_tab.py`, `tests/test_gui_psd_tab.py`, `tests/test_gui_db.py`,
  `tests/test_gui_replay.py`, `tests/test_copolymerization_assistant.py`.

---

### M58. Workshop Example Reproduction Benchmarks

#### Scope
워크숍 7(Examples) + 튜토리얼의 대표 예제를 벤치마크로 재현해 전 서브시스템을 교차검증.

#### Requirements
- `validation/benchmarks/`에 추가:
  - **Oregonator**(기존, 유지) + **CamelBack/FoxHole/Scaling**(PE 테스트 케이스).
  - **ATRP.xml** 상당(controlled MWD), **cascade_by_tank**(Cunningham, copyreactor).
  - **Condensation series**(MC + end-group), **Copolymerization series**(±MC),
    **Crosslinking series**(gel point, 두 수치 접근).
  - **Ethene gel effect**(heat balance + 스크립트 procedures).
  - **Emulsion_Polymerization_MC**(다상 + MC), **DME_Fugacities**(fugacity DB).
  - **MSMPR 결정화**, **PSD growth/nucleation**.
- `validation/benchmark_runner.py`에 fast/medium/slow 등급 편입.

#### Acceptance Criteria
- 각 벤치마크가 문헌/원본 정성거동(gel point 위치, 조성 드리프트, MWD 형상, 진동 등)을 허용오차 내 재현.

#### Tests
- `tests/test_workshop_benchmarks.py`.

---

### M58b. `test_manuals/` — 통합 실행 프로그램 (Manual Reproduction Suite)

#### Scope
`datas/`의 **39개 PDF에 제시된 모든 기능을 실제로 돌려보는 단일 실행 프로그램**을 프로젝트 루트의
`test_manuals/` 디렉터리에 만든다. M58의 `validation/benchmarks`가 "정확도 회귀"에 초점이라면,
`test_manuals/`는 **사용자 관점의 재현 러너**다 — 각 매뉴얼/기능을 스크립트 하나로 실행하고, 결과
(수치·그림·리포트)를 생성하며, CLI로 개별/전체 실행을 지원한다. plan6의 M41~M58 백엔드가 완성되어
갈수록 이 러너의 커버리지가 채워지도록 **점진적 등록** 구조로 만든다.

#### 디렉터리 구조
```
test_manuals/
├── __init__.py
├── __main__.py            # python -m test_manuals 진입점(CLI)
├── runner.py              # 예제 등록/필터/실행/타이밍/집계
├── registry.py            # ManualExample 데이터클래스 + 데코레이터 등록
├── report.py              # HTML/Markdown 리포트 + 그림 임베드
├── cli.py                 # --all / --pdf / --feature / --milestone / --list / --smoke
├── examples/
│   ├── core/              # Galerkin, 모멘트, 적응격자 (Predici7 매뉴얼)
│   ├── reactors/          # batch/semibatch/CSTR/PFR/cascade/MSMPR + heat balance
│   ├── frp/               # 폴리에틸렌 튜토리얼, glass/gel effect
│   ├── crp/               # ATRP/RAFT/NMP (Fu ATRP, exercise_atrp)
│   ├── stepgrowth/        # polycondensation AA-BB/AA-DD, condensation flags
│   ├── crosslink/         # CrossLinkingModels, gel point, FGD (Hutchinson)
│   ├── copolymer/         # terminal/penultimate/N-monomer, composition drift
│   ├── montecarlo/        # hybrid MC, tau-leaping, topology, SLA (MC PDFs)
│   ├── psd/               # PrediciPSD_Tutorial: growth/nucleation/breakage/agglomeration, MSMPR
│   ├── emulsion/          # Smith-Ewart, Df, rho-c (Emulsion workshops)
│   ├── thermo/            # fugacities, PT flash, mix density (Fugacities, Cape-Open)
│   ├── fitting/           # PE 예제(CamelBack/FoxHole/Scaling), MDF, Arrhenius plot
│   ├── kinetics/          # Presto-Kinetics: Oregonator, Langmuir-Hinshelwood, ODE-system
│   ├── replay/            # replay 기록/재생
│   └── automation/        # automation API/자동화 서버 워크플로
├── outputs/               # 실행 산출물(그림/CSV/NPZ/리포트) — .gitignore
└── README.md              # 사용법 + PDF↔예제 매핑 표
```

#### Requirements
- `registry.py`: `ManualExample` 데이터클래스 — `id`, `title`, `source_pdf`(원본 PDF 파일명),
  `feature`(도메인 태그), `milestone`(대응 M41~M58), `run()`(콜러블), `expected`(선택적 검증 기준),
  `requires`(의존 서브시스템 feature flag). `@manual_example(...)` 데코레이터로 자동 등록.
- 각 `examples/**/*.py`는 **최소 하나의 재현 예제**를 등록한다. 예제는 프로젝트를 코드로 구성 →
  시뮬 실행 → 핵심 출력(모멘트/전환율/분포/gel point/조성/PSD 모멘트 등) 산출 → `outputs/`에 그림·
  데이터 저장. 원본 PDF의 해당 그림/표를 재현하는 것을 목표로 하되, 정성거동 일치를 1차 기준으로 한다.
- `runner.py`: 등록된 예제 필터/실행, 예제별 상태(PASS/FAIL/SKIP-미구현), 소요시간, 예외 캡처.
  아직 미구현(feature flag off) 예제는 **SKIP(사유: milestone Mxx 대기)**로 표기(실패로 취급하지 않음).
- `cli.py` / `__main__.py`:
  - `python -m test_manuals --list` — 등록된 전 예제와 PDF/feature/milestone 매핑 출력.
  - `python -m test_manuals --all` — 전체 실행 + `outputs/report.html` 생성.
  - `python -m test_manuals --pdf "PrediciPSD_Tutorial_2017"` — 특정 PDF 관련 예제만.
  - `python -m test_manuals --feature montecarlo` / `--milestone M42`.
  - `python -m test_manuals --smoke` — 빠른(fast 등급) 대표 예제만.
- `report.py`: 실행 결과를 HTML/Markdown로 — PDF별 섹션, 예제별 상태·시간·핵심 수치·임베드 그림,
  전체 커버리지 요약(구현/미구현/PDF 커버리지 %).
- `README.md`: **39개 PDF ↔ 예제 매핑 표**(각 PDF의 어떤 기능을 어떤 예제가 커버하는지)와 실행법.
- GUI가 아닌 **headless** 실행(Matplotlib Agg 백엔드)으로 CI/패키징에서도 무헤드 동작.
- `test_manuals` 자체의 스모크는 `tests/test_manual_suite.py`로 회귀 편입(등록 무결성 + `--smoke` 통과).

#### PDF ↔ 예제 커버리지 목표
39개 PDF 각각에 대해 **최소 1개 이상의 실행 예제**가 존재하도록 한다(버전 릴리스 노트류는 대표 신규
기능 1개 예제로 대응 가능). `--list`의 커버리지 요약에서 "PDF coverage = 커버된 PDF 수 / 39"를 보고한다.

#### Acceptance Criteria
- `python -m test_manuals --all`이 오류 없이 완주하고 `outputs/report.html`을 생성한다.
- 구현 완료된 서브시스템(M41~M58) 예제는 전부 PASS, 미구현은 명시적 SKIP(사유 포함)로 분류된다.
- `--list`가 39개 PDF 전체가 최소 1개 예제로 매핑됨을 보고한다(PDF coverage 100%).
- `--smoke`가 fast 대표 예제만 짧게 실행된다.

#### Tests
- `tests/test_manual_suite.py` — 레지스트리 무결성(모든 예제가 유효 PDF/milestone 참조),
  `--list`/`--smoke` 실행, report 생성 검증.

> 주: `test_manuals/`는 M41부터 각 마일스톤과 **병행 성장**한다. 각 마일스톤 완료 시 해당 예제를
> `examples/`에 즉시 등록하고 SKIP→PASS로 전환한다. M58b는 이 러너/CLI/리포트 인프라의 **완성 및
> 전체 커버리지 확정** 시점이다.

---

### M59. Packaging & Docs v2.0

#### Scope
확장된 코드베이스를 재패키징하고 매뉴얼을 갱신.

#### Requirements
- PyInstaller spec 갱신(MC/PSD/thermo 신규 의존: networkx/graphviz/openpyxl 포함), clean-venv 빌드.
- 매뉴얼 신규 챕터: Monte-Carlo, PSD/Emulsion, Cape-Open/Fugacity, Parameter DB, Replay, Optimal
  control, 확장 스크립트 레퍼런스, **`test_manuals/` 사용법 챕터**.
- `dist/PrediciClone/` 스모크 체크리스트에 MC/PSD/fugacity 예제 실행 추가.
- 패키징 산출물에 `test_manuals --smoke`가 실행 가능하도록 포함(선택적 콘솔 엔트리포인트).

#### Acceptance Criteria
- clean 환경 exe가 추가 설치 없이 MC/PSD/fugacity 예제를 실행.
- `sphinx-build -W` 경고 없이 통과.

#### Tests
- `scripts/packaging_smoke_test_v2.ps1`.

---

### M60. v2.0 Regression Freeze

#### Scope
M41~M59 통합 최종 검증·문서 동결.

#### Requirements
- 전체 벤치마크(fast/medium/slow) 실행·`docs/v2_benchmark_report.md` 기록.
- `pytest -q` 전체(core/reactor/kinetics/MC/PSD/emulsion/thermo/DB/fitting/optimal/replay/GUI/interop)
  통과, `docs/v2_ci_report.md` 첨부.
- `CHANGELOG.md` v2.0.0 작성, 태그 `v2.0.0`.

#### Acceptance Criteria
- 전 회귀 스위트 + 매뉴얼 빌드 + 패키징 스모크 통과.
- plan6 Completion Criteria(아래 6절) 전부 충족.

#### Tests
- 전체 회귀 CI 로그.

---

## 5. Implementation Order

의존성 기반 권장 순서:

1. **M41 Reaction step 라이브러리** — 이후 거의 모든 화학/PDE 기능의 토대.
2. **M42 → M43 Monte-Carlo** — 최대 리스크·최대 가치. 조기 착수해 안정화.
3. **M44 CRP/step-growth 화학** — MC(토폴로지/FGD)와 결합해 검증.
4. **M47 다상 반응기** → **M45 PSD** → **M46 Emulsion** — 다상이 PSD/emulsion의 전제.
5. **M48 Fugacity/Cape-Open** — 다상 열역학 완성(M47/M55와 연동).
6. **M49 Parameter DB/sets** — 화학·열역학 파라미터 대량화 이후.
7. **M50 PE 완결** → **M51 Optimal control/Variation** — fitting 인프라 확장.
8. **M52 Replay**, **M53 IDS/generator**, **M54 Scripting/PID** — 워크플로 편의(병렬 가능).
9. **M55 Heat/feed 확장** — 반응기 물리 마감.
10. **M56 Interoperability** → **M57 GUI 통합** — 백엔드 완성 후 통합.
11. **M58 벤치마크** → **M58b `test_manuals/` 러너 완성** → **M59 패키징** → **M60 freeze**.

> `test_manuals/`의 러너/CLI/리포트 인프라(뼈대)는 **M41 직후 조기 구축**하고, 각 마일스톤 완료 시
> 예제를 등록해 나간다(SKIP→PASS). M58b는 완성·전체 커버리지 확정 시점이다.

---

## 6. Risks

### Risk: Monte-Carlo 엔진의 결정론 엔진 결합이 광범위한 계약 변경을 유발
Mitigation: MC를 **결정론 적분 루프의 후처리 훅**(스텝별 콜백)으로 설계해 기존 적분기/Galerkin
백엔드를 수정하지 않는다. MC off 경로가 항상 기존 결과와 동치임을 회귀 테스트로 고정.

### Risk: PSD/PBE의 method-of-lines가 대형 희소계로 성능 폭증
Mitigation: 초기에는 고정 격자 + 희소 자코비안(기존 `integrator/jacobian.py` 재사용), 적응격자는
후속. 질량보존을 1차 accept 기준으로 삼아 정확도 우선.

### Risk: 95개 reaction step의 balance 파생 오류가 조용히 전파
Mitigation: 스텝별 단일 스텝 해석해 유닛 테스트를 M41에서 강제하고, 복합 스킴은 balance
자동검산(mass/moment) 경고를 켠다.

### Risk: Cape-Open 실제 COM 서버 의존
Mitigation: 자체 Peng-Robinson EOS와 in-process 어댑터로 핵심 기능(fugacity/flash/mix density)을
구현하고, 실제 COCO/Multiflash 연결은 선택적 어댑터로 분리(비목표 유지).

### Risk: OLE/COM 자동화 서버가 Windows COM 등록 등 플랫폼 의존
Mitigation: Python in-process automation API를 1차 산출물로 하고 COM 래퍼는 선택적. 계약 테스트는
Python API 기준.

### Risk: 범위가 매우 커서 부분 완료 상태로 정체
Mitigation: 각 마일스톤을 독립 병합 가능 단위로 유지(각자 테스트/벤치마크 동반), 서브시스템별
feature flag로 미완 기능이 기존 v1.0 경로를 깨지 않도록 격리.

---

## 7. Plan6 Completion Criteria

Plan6는 다음이 모두 충족되면 완료된다.

1. 95개 reaction step 계열이 라이브러리로 제공되고 스텝별 balance 테스트를 통과한다 (M41).
2. Hybrid Monte-Carlo 엔진이 결정론 CLD/모멘트와 지정오차 내 일치하고 `getmcinfo/getmcaverage`가
   동작한다 (M42).
3. tau-leaping/topology(gyration)/sequence length analysis/backward coupling이 벤치마크를
   통과한다 (M43).
4. ATRP/RAFT/NMP, polycondensation(AA-BB/AA-DD), crosslinking(gel point), FGD, penultimate/
   N-monomer copolymer, glass/gel effect가 각 벤치마크를 통과한다 (M44).
5. PSD/PBE(nucleation/growth/breakage/agglomeration)와 MSMPR가 해석해/질량보존 검증을 통과한다 (M45).
6. Emulsion(Smith-Ewart, Df, rho-c, entry/exit, partitioning)이 극한 케이스를 재현한다 (M46).
7. 다상 반응기와 phase exchange(partition/solubility/precipitation)가 질량·부피 수지를 보존한다 (M47).
8. Peng-Robinson fugacity/PT flash/co_* 커맨드/mix density가 DME fugacity 벤치마크를 통과한다 (M48).
9. Parameter DB(dbpar/dbfunc)와 parameter/module set/group 전환이 계약 테스트를 통과한다 (M49).
10. MDF/reduced-directions/IND/box search/parity·3D/Arrhenius plot/robust optimization이
    동작한다 (M50).
11. Optimal control(시간최적/프로파일)과 variation tool이 목표에 수렴한다 (M51).
12. Replay 재생 결과가 원 시뮬과 동등하고 output-on-replay/MC-from-replay가 동작한다 (M52).
13. IDS/AST 재사용과 Schulz-Flory/Poisson/custom distribution generator가 동작한다 (M53).
14. PID/procedures/전체 interpreter 함수(co_*/db*/getprofmy/getmcinfo/copyreactor 등)와
    ODE-system 스텝, 스크립트 디버거가 동작한다 (M54).
15. user-defined heat balance/cp-derivative/feed temperature/mass stream table/variable pressure가
    동작한다 (M55).
16. Python automation API, Excel export, flowsheet, Petri chart, model 비교/교환이 동작한다 (M56).
17. 신규 서브시스템 GUI(MC/PSD/Emulsion/DB/Replay/copolymerization assistant)가 모달 깊이 2단 이하로
    통합된다 (M57).
18. 워크숍 예제 벤치마크(ATRP/emulsion/gel/MSMPR/DME/MC/PSD)가 정성거동을 재현한다 (M58).
19. `test_manuals/` 프로그램이 `python -m test_manuals --all`로 완주하고, 39개 PDF 전체가 최소 1개
    예제로 매핑(PDF coverage 100%)되며, 구현분은 PASS·미구현분은 명시적 SKIP으로 리포트된다 (M58b).
20. Windows PyInstaller v2.0 빌드가 clean 환경에서 MC/PSD/fugacity 예제 스모크를 통과한다 (M59).
21. 전체 회귀 스위트와 매뉴얼 빌드가 통과하고 `v2.0.0` 태그가 생성된다 (M60).
