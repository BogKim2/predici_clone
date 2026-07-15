# test_manual_result

이 디렉터리는 39개 PDF 매뉴얼 재현 시나리오의 전체 실행 결과입니다.

- 결과: **PASS 39 / FAIL 0 / SKIP 0**
- PDF 커버리지: **39 / 39 (100.00%)**
- 실행 명령: `python -m test_manuals --all --split --output .\test_manual_result`
- 생성 시각(UTC): `2026-07-15T10:34:28.974540+00:00`

## 파일

- [report.html](report.html): feature, milestone, PDF별 브라우저 보고서
- [report.md](report.md): PDF별 지표와 기대 범위를 모두 포함한 Markdown 보고서
- [results.json](results.json): 실행 환경, 집계, 개별 결과를 포함한 구조화 데이터
- [results.csv](results.csv): PDF당 한 행으로 정리한 스프레드시트용 결과

## PDF와 시나리오 매핑

| PDF | Example ID | Feature | Milestone | Status |
| --- | --- | --- | --- | --- |
| CiT Parameter Estimation.pdf | `cit_parameter_estimation` | `fitting` | `M50` | **PASS** |
| CrossLinkingModels.pdf | `crosslinkingmodels` | `crosslink` | `M44` | **PASS** |
| eGAS.pdf | `egas` | `thermo` | `M48` | **PASS** |
| exercise_atrp.pdf | `exercise_atrp` | `crp` | `M44` | **PASS** |
| Feed and heat balance v2.pdf | `feed_and_heat_balance_v2` | `reactors` | `M55` | **PASS** |
| Fu ATRP MRE.pdf | `fu_atrp_mre` | `crp` | `M44` | **PASS** |
| Fugacities in Predici and Presto Kinetics.pdf | `fugacities_in_predici_and_presto_kinetics` | `thermo` | `M48` | **PASS** |
| Hutchinson_Wulkow_et_el_Functional_group_distribution_2014.pdf | `hutchinson_wulkow_et_el_functional_group_distribution_2014` | `crosslink` | `M44` | **PASS** |
| ListOfModels.pdf | `listofmodels` | `kinetics` | `M41` | **PASS** |
| New Condensation Flags.pdf | `new_condensation_flags` | `stepgrowth` | `M44` | **PASS** |
| Polycondensation of AA_DD.pdf | `polycondensation_of_aa_dd` | `stepgrowth` | `M44` | **PASS** |
| Predici and Presto-Kinetics - All Documents.pdf | `predici_and_presto_kinetics_all_documents` | `kinetics` | `M41` | **PASS** |
| Predici Parameter Estimation.pdf | `predici_parameter_estimation` | `fitting` | `M50` | **PASS** |
| Predici Version_11_16_1_20170717.pdf | `predici_version_11_16_1_20170717` | `kinetics` | `M41` | **PASS** |
| Predici11 Polymer Tutorial.pdf | `predici11_polymer_tutorial` | `crp` | `M44` | **PASS** |
| Predici11_Cape-Open.pdf | `predici11_cape_open` | `thermo` | `M48` | **PASS** |
| Predici11_Hybrid-Monte-Carlo.pdf | `predici11_hybrid_monte_carlo` | `montecarlo` | `M42` | **PASS** |
| Predici11_Kinetic_Model.pdf | `predici11_kinetic_model` | `kinetics` | `M41` | **PASS** |
| Predici11_Tutorials.pdf | `predici11_tutorials` | `kinetics` | `M41` | **PASS** |
| Predici11_Workshop_November_2016_1. Presto-Kinetics.pdf | `predici11_workshop_november_2016_1_presto_kinetics` | `kinetics` | `M41` | **PASS** |
| Predici11_Workshop_November_2016_2. Parameter_Estimation.pdf | `predici11_workshop_november_2016_2_parameter_estimation` | `fitting` | `M50` | **PASS** |
| Predici11_Workshop_November_2016_3. Polymers1.pdf | `predici11_workshop_november_2016_3_polymers1` | `kinetics` | `M41` | **PASS** |
| Predici11_Workshop_November_2016_4. Polymers2 .pdf | `predici11_workshop_november_2016_4_polymers2` | `kinetics` | `M41` | **PASS** |
| Predici11_Workshop_November_2016_5. Monte-Carlo_Details.pdf | `predici11_workshop_november_2016_5_monte_carlo_details` | `montecarlo` | `M42` | **PASS** |
| Predici11_Workshop_November_2016_6. Emulsion_Polymerization.pdf | `predici11_workshop_november_2016_6_emulsion_polymerization` | `emulsion` | `M46` | **PASS** |
| Predici11_Workshop_November_2016_7. Examples.pdf | `predici11_workshop_november_2016_7_examples` | `kinetics` | `M41` | **PASS** |
| Predici7_Manual.pdf | `predici7_manual` | `kinetics` | `M41` | **PASS** |
| PrediciPSD_Tutorial_2017.pdf | `predicipsd_tutorial_2017` | `psd` | `M45` | **PASS** |
| Presto11 Parameter Estimation.pdf | `presto11_parameter_estimation` | `fitting` | `M50` | **PASS** |
| Procedures in Predici.pdf | `procedures_in_predici` | `automation` | `M54` | **PASS** |
| Schuette-Wulkow_Predici-MonteCarlo.pdf | `schuette_wulkow_predici_montecarlo` | `montecarlo` | `M42` | **PASS** |
| Version_11_13_3.pdf | `version_11_13_3` | `replay` | `M52` | **PASS** |
| Version_11_14_3.pdf | `version_11_14_3` | `reactors` | `M55` | **PASS** |
| Version_11_14_5.pdf | `version_11_14_5` | `reactors` | `M55` | **PASS** |
| Version_11_15_1_Parameter_Sets and DB.pdf | `version_11_15_1_parameter_sets_and_db` | `database` | `M49` | **PASS** |
| Wulkow - Emulsion - Workshop - Final_Slides.pdf | `wulkow_emulsion_workshop_final_slides` | `emulsion` | `M46` | **PASS** |
| Wulkow-The Status of Predici.pdf | `wulkow_the_status_of_predici` | `kinetics` | `M41` | **PASS** |
| Predici11_Overview.pdf | `predici11_overview` | `kinetics` | `M41` | **PASS** |
| Predici_Maxwell.pdf | `predici_maxwell` | `montecarlo` | `M42` | **PASS** |

## 개별 테스트 폴더

각 번호 폴더의 `run_test.ps1` 또는 `run_test.cmd`를 실행하면 해당 PDF 한 건만 다시 계산하고 결과를 같은 폴더에 저장합니다.

| 번호 | PDF | Example ID | Feature | Milestone | Status |
| ---: | --- | --- | --- | --- | --- |
| [1](1/README.md) | CiT Parameter Estimation.pdf | `cit_parameter_estimation` | `fitting` | `M50` | **PASS** |
| [2](2/README.md) | CrossLinkingModels.pdf | `crosslinkingmodels` | `crosslink` | `M44` | **PASS** |
| [3](3/README.md) | eGAS.pdf | `egas` | `thermo` | `M48` | **PASS** |
| [4](4/README.md) | exercise_atrp.pdf | `exercise_atrp` | `crp` | `M44` | **PASS** |
| [5](5/README.md) | Feed and heat balance v2.pdf | `feed_and_heat_balance_v2` | `reactors` | `M55` | **PASS** |
| [6](6/README.md) | Fu ATRP MRE.pdf | `fu_atrp_mre` | `crp` | `M44` | **PASS** |
| [7](7/README.md) | Fugacities in Predici and Presto Kinetics.pdf | `fugacities_in_predici_and_presto_kinetics` | `thermo` | `M48` | **PASS** |
| [8](8/README.md) | Hutchinson_Wulkow_et_el_Functional_group_distribution_2014.pdf | `hutchinson_wulkow_et_el_functional_group_distribution_2014` | `crosslink` | `M44` | **PASS** |
| [9](9/README.md) | ListOfModels.pdf | `listofmodels` | `kinetics` | `M41` | **PASS** |
| [10](10/README.md) | New Condensation Flags.pdf | `new_condensation_flags` | `stepgrowth` | `M44` | **PASS** |
| [11](11/README.md) | Polycondensation of AA_DD.pdf | `polycondensation_of_aa_dd` | `stepgrowth` | `M44` | **PASS** |
| [12](12/README.md) | Predici and Presto-Kinetics - All Documents.pdf | `predici_and_presto_kinetics_all_documents` | `kinetics` | `M41` | **PASS** |
| [13](13/README.md) | Predici Parameter Estimation.pdf | `predici_parameter_estimation` | `fitting` | `M50` | **PASS** |
| [14](14/README.md) | Predici Version_11_16_1_20170717.pdf | `predici_version_11_16_1_20170717` | `kinetics` | `M41` | **PASS** |
| [15](15/README.md) | Predici11 Polymer Tutorial.pdf | `predici11_polymer_tutorial` | `crp` | `M44` | **PASS** |
| [16](16/README.md) | Predici11_Cape-Open.pdf | `predici11_cape_open` | `thermo` | `M48` | **PASS** |
| [17](17/README.md) | Predici11_Hybrid-Monte-Carlo.pdf | `predici11_hybrid_monte_carlo` | `montecarlo` | `M42` | **PASS** |
| [18](18/README.md) | Predici11_Kinetic_Model.pdf | `predici11_kinetic_model` | `kinetics` | `M41` | **PASS** |
| [19](19/README.md) | Predici11_Tutorials.pdf | `predici11_tutorials` | `kinetics` | `M41` | **PASS** |
| [20](20/README.md) | Predici11_Workshop_November_2016_1. Presto-Kinetics.pdf | `predici11_workshop_november_2016_1_presto_kinetics` | `kinetics` | `M41` | **PASS** |
| [21](21/README.md) | Predici11_Workshop_November_2016_2. Parameter_Estimation.pdf | `predici11_workshop_november_2016_2_parameter_estimation` | `fitting` | `M50` | **PASS** |
| [22](22/README.md) | Predici11_Workshop_November_2016_3. Polymers1.pdf | `predici11_workshop_november_2016_3_polymers1` | `kinetics` | `M41` | **PASS** |
| [23](23/README.md) | Predici11_Workshop_November_2016_4. Polymers2 .pdf | `predici11_workshop_november_2016_4_polymers2` | `kinetics` | `M41` | **PASS** |
| [24](24/README.md) | Predici11_Workshop_November_2016_5. Monte-Carlo_Details.pdf | `predici11_workshop_november_2016_5_monte_carlo_details` | `montecarlo` | `M42` | **PASS** |
| [25](25/README.md) | Predici11_Workshop_November_2016_6. Emulsion_Polymerization.pdf | `predici11_workshop_november_2016_6_emulsion_polymerization` | `emulsion` | `M46` | **PASS** |
| [26](26/README.md) | Predici11_Workshop_November_2016_7. Examples.pdf | `predici11_workshop_november_2016_7_examples` | `kinetics` | `M41` | **PASS** |
| [27](27/README.md) | Predici7_Manual.pdf | `predici7_manual` | `kinetics` | `M41` | **PASS** |
| [28](28/README.md) | PrediciPSD_Tutorial_2017.pdf | `predicipsd_tutorial_2017` | `psd` | `M45` | **PASS** |
| [29](29/README.md) | Presto11 Parameter Estimation.pdf | `presto11_parameter_estimation` | `fitting` | `M50` | **PASS** |
| [30](30/README.md) | Procedures in Predici.pdf | `procedures_in_predici` | `automation` | `M54` | **PASS** |
| [31](31/README.md) | Schuette-Wulkow_Predici-MonteCarlo.pdf | `schuette_wulkow_predici_montecarlo` | `montecarlo` | `M42` | **PASS** |
| [32](32/README.md) | Version_11_13_3.pdf | `version_11_13_3` | `replay` | `M52` | **PASS** |
| [33](33/README.md) | Version_11_14_3.pdf | `version_11_14_3` | `reactors` | `M55` | **PASS** |
| [34](34/README.md) | Version_11_14_5.pdf | `version_11_14_5` | `reactors` | `M55` | **PASS** |
| [35](35/README.md) | Version_11_15_1_Parameter_Sets and DB.pdf | `version_11_15_1_parameter_sets_and_db` | `database` | `M49` | **PASS** |
| [36](36/README.md) | Wulkow - Emulsion - Workshop - Final_Slides.pdf | `wulkow_emulsion_workshop_final_slides` | `emulsion` | `M46` | **PASS** |
| [37](37/README.md) | Wulkow-The Status of Predici.pdf | `wulkow_the_status_of_predici` | `kinetics` | `M41` | **PASS** |
| [38](38/README.md) | Predici11_Overview.pdf | `predici11_overview` | `kinetics` | `M41` | **PASS** |
| [39](39/README.md) | Predici_Maxwell.pdf | `predici_maxwell` | `montecarlo` | `M42` | **PASS** |
