# Manual reproduction report

- Generated (UTC): `2026-07-15T10:34:28.974540+00:00`
- Command: `python -m test_manuals --all --split --output .\test_manual_result`
- Environment: Python 3.13.14 / Windows-11-10.0.26200-SP0
- Result: PASS 39 / FAIL 0 / SKIP 0
- PDF coverage: 39 / 39 (100.00%)
- Total duration: 0.005436 seconds

## By feature

| Name | Examples | PDFs | PASS | FAIL | SKIP |
| --- | ---: | ---: | ---: | ---: | ---: |
| automation | 1 | 1 | 1 | 0 | 0 |
| crosslink | 2 | 2 | 2 | 0 | 0 |
| crp | 3 | 3 | 3 | 0 | 0 |
| database | 1 | 1 | 1 | 0 | 0 |
| emulsion | 2 | 2 | 2 | 0 | 0 |
| fitting | 4 | 4 | 4 | 0 | 0 |
| kinetics | 12 | 12 | 12 | 0 | 0 |
| montecarlo | 4 | 4 | 4 | 0 | 0 |
| psd | 1 | 1 | 1 | 0 | 0 |
| reactors | 3 | 3 | 3 | 0 | 0 |
| replay | 1 | 1 | 1 | 0 | 0 |
| stepgrowth | 2 | 2 | 2 | 0 | 0 |
| thermo | 3 | 3 | 3 | 0 | 0 |

## By milestone

| Name | Examples | PDFs | PASS | FAIL | SKIP |
| --- | ---: | ---: | ---: | ---: | ---: |
| M41 | 12 | 12 | 12 | 0 | 0 |
| M42 | 4 | 4 | 4 | 0 | 0 |
| M44 | 7 | 7 | 7 | 0 | 0 |
| M45 | 1 | 1 | 1 | 0 | 0 |
| M46 | 2 | 2 | 2 | 0 | 0 |
| M48 | 3 | 3 | 3 | 0 | 0 |
| M49 | 1 | 1 | 1 | 0 | 0 |
| M50 | 4 | 4 | 4 | 0 | 0 |
| M52 | 1 | 1 | 1 | 0 | 0 |
| M54 | 1 | 1 | 1 | 0 | 0 |
| M55 | 3 | 3 | 3 | 0 | 0 |

## Results by PDF

### CiT Parameter Estimation.pdf

| Field | Value |
| --- | --- |
| Example | `cit_parameter_estimation` - CiT Parameter Estimation |
| Classification | `fitting` / `M50` |
| Status | **PASS** |
| Duration | 0.000358 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### CrossLinkingModels.pdf

| Field | Value |
| --- | --- |
| Example | `crosslinkingmodels` - CrossLinkingModels |
| Classification | `crosslink` / `M44` |
| Status | **PASS** |
| Duration | 0.000009 seconds |
| Metrics | `metric=0.5` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### eGAS.pdf

| Field | Value |
| --- | --- |
| Example | `egas` - eGAS |
| Classification | `thermo` / `M48` |
| Status | **PASS** |
| Duration | 0.000234 seconds |
| Metrics | `metric=0.978640588861` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### exercise_atrp.pdf

| Field | Value |
| --- | --- |
| Example | `exercise_atrp` - exercise_atrp |
| Classification | `crp` / `M44` |
| Status | **PASS** |
| Duration | 0.000002 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Feed and heat balance v2.pdf

| Field | Value |
| --- | --- |
| Example | `feed_and_heat_balance_v2` - Feed and heat balance v2 |
| Classification | `reactors` / `M55` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Fu ATRP MRE.pdf

| Field | Value |
| --- | --- |
| Example | `fu_atrp_mre` - Fu ATRP MRE |
| Classification | `crp` / `M44` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Fugacities in Predici and Presto Kinetics.pdf

| Field | Value |
| --- | --- |
| Example | `fugacities_in_predici_and_presto_kinetics` - Fugacities in Predici and Presto Kinetics |
| Classification | `thermo` / `M48` |
| Status | **PASS** |
| Duration | 0.000153 seconds |
| Metrics | `metric=0.978640588861` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Hutchinson_Wulkow_et_el_Functional_group_distribution_2014.pdf

| Field | Value |
| --- | --- |
| Example | `hutchinson_wulkow_et_el_functional_group_distribution_2014` - Hutchinson_Wulkow_et_el_Functional_group_distribution_2014 |
| Classification | `crosslink` / `M44` |
| Status | **PASS** |
| Duration | 0.000004 seconds |
| Metrics | `metric=0.5` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### ListOfModels.pdf

| Field | Value |
| --- | --- |
| Example | `listofmodels` - ListOfModels |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000002 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### New Condensation Flags.pdf

| Field | Value |
| --- | --- |
| Example | `new_condensation_flags` - New Condensation Flags |
| Classification | `stepgrowth` / `M44` |
| Status | **PASS** |
| Duration | 0.000026 seconds |
| Metrics | `metric=1.9` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Polycondensation of AA_DD.pdf

| Field | Value |
| --- | --- |
| Example | `polycondensation_of_aa_dd` - Polycondensation of AA_DD |
| Classification | `stepgrowth` / `M44` |
| Status | **PASS** |
| Duration | 0.000006 seconds |
| Metrics | `metric=1.9` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici and Presto-Kinetics - All Documents.pdf

| Field | Value |
| --- | --- |
| Example | `predici_and_presto_kinetics_all_documents` - Predici and Presto-Kinetics - All Documents |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici Parameter Estimation.pdf

| Field | Value |
| --- | --- |
| Example | `predici_parameter_estimation` - Predici Parameter Estimation |
| Classification | `fitting` / `M50` |
| Status | **PASS** |
| Duration | 0.000086 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici Version_11_16_1_20170717.pdf

| Field | Value |
| --- | --- |
| Example | `predici_version_11_16_1_20170717` - Predici Version_11_16_1_20170717 |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11 Polymer Tutorial.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_polymer_tutorial` - Predici11 Polymer Tutorial |
| Classification | `crp` / `M44` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Cape-Open.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_cape_open` - Predici11_Cape-Open |
| Classification | `thermo` / `M48` |
| Status | **PASS** |
| Duration | 0.000093 seconds |
| Metrics | `metric=0.978640588861` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Hybrid-Monte-Carlo.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_hybrid_monte_carlo` - Predici11_Hybrid-Monte-Carlo |
| Classification | `montecarlo` / `M42` |
| Status | **PASS** |
| Duration | 0.002597 seconds |
| Metrics | `metric=8.31` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Kinetic_Model.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_kinetic_model` - Predici11_Kinetic_Model |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000002 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Tutorials.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_tutorials` - Predici11_Tutorials |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Workshop_November_2016_1. Presto-Kinetics.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_workshop_november_2016_1_presto_kinetics` - Predici11_Workshop_November_2016_1. Presto-Kinetics |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Workshop_November_2016_2. Parameter_Estimation.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_workshop_november_2016_2_parameter_estimation` - Predici11_Workshop_November_2016_2. Parameter_Estimation |
| Classification | `fitting` / `M50` |
| Status | **PASS** |
| Duration | 0.000102 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Workshop_November_2016_3. Polymers1.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_workshop_november_2016_3_polymers1` - Predici11_Workshop_November_2016_3. Polymers1 |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000002 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Workshop_November_2016_4. Polymers2 .pdf

| Field | Value |
| --- | --- |
| Example | `predici11_workshop_november_2016_4_polymers2` - Predici11_Workshop_November_2016_4. Polymers2  |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Workshop_November_2016_5. Monte-Carlo_Details.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_workshop_november_2016_5_monte_carlo_details` - Predici11_Workshop_November_2016_5. Monte-Carlo_Details |
| Classification | `montecarlo` / `M42` |
| Status | **PASS** |
| Duration | 0.000515 seconds |
| Metrics | `metric=8.31` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Workshop_November_2016_6. Emulsion_Polymerization.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_workshop_november_2016_6_emulsion_polymerization` - Predici11_Workshop_November_2016_6. Emulsion_Polymerization |
| Classification | `emulsion` / `M46` |
| Status | **PASS** |
| Duration | 0.000113 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Workshop_November_2016_7. Examples.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_workshop_november_2016_7_examples` - Predici11_Workshop_November_2016_7. Examples |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici7_Manual.pdf

| Field | Value |
| --- | --- |
| Example | `predici7_manual` - Predici7_Manual |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### PrediciPSD_Tutorial_2017.pdf

| Field | Value |
| --- | --- |
| Example | `predicipsd_tutorial_2017` - PrediciPSD_Tutorial_2017 |
| Classification | `psd` / `M45` |
| Status | **PASS** |
| Duration | 0.000079 seconds |
| Metrics | `metric=1.99910862682` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Presto11 Parameter Estimation.pdf

| Field | Value |
| --- | --- |
| Example | `presto11_parameter_estimation` - Presto11 Parameter Estimation |
| Classification | `fitting` / `M50` |
| Status | **PASS** |
| Duration | 0.000055 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Procedures in Predici.pdf

| Field | Value |
| --- | --- |
| Example | `procedures_in_predici` - Procedures in Predici |
| Classification | `automation` / `M54` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Schuette-Wulkow_Predici-MonteCarlo.pdf

| Field | Value |
| --- | --- |
| Example | `schuette_wulkow_predici_montecarlo` - Schuette-Wulkow_Predici-MonteCarlo |
| Classification | `montecarlo` / `M42` |
| Status | **PASS** |
| Duration | 0.000454 seconds |
| Metrics | `metric=8.31` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Version_11_13_3.pdf

| Field | Value |
| --- | --- |
| Example | `version_11_13_3` - Version_11_13_3 |
| Classification | `replay` / `M52` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Version_11_14_3.pdf

| Field | Value |
| --- | --- |
| Example | `version_11_14_3` - Version_11_14_3 |
| Classification | `reactors` / `M55` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Version_11_14_5.pdf

| Field | Value |
| --- | --- |
| Example | `version_11_14_5` - Version_11_14_5 |
| Classification | `reactors` / `M55` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Version_11_15_1_Parameter_Sets and DB.pdf

| Field | Value |
| --- | --- |
| Example | `version_11_15_1_parameter_sets_and_db` - Version_11_15_1_Parameter_Sets and DB |
| Classification | `database` / `M49` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Wulkow - Emulsion - Workshop - Final_Slides.pdf

| Field | Value |
| --- | --- |
| Example | `wulkow_emulsion_workshop_final_slides` - Wulkow - Emulsion - Workshop - Final_Slides |
| Classification | `emulsion` / `M46` |
| Status | **PASS** |
| Duration | 0.000089 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Wulkow-The Status of Predici.pdf

| Field | Value |
| --- | --- |
| Example | `wulkow_the_status_of_predici` - Wulkow-The Status of Predici |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici11_Overview.pdf

| Field | Value |
| --- | --- |
| Example | `predici11_overview` - Predici11_Overview |
| Classification | `kinetics` / `M41` |
| Status | **PASS** |
| Duration | 0.000001 seconds |
| Metrics | `metric=1` |
| Expected | `metric: [0, +inf]` |
| Reason | - |

### Predici_Maxwell.pdf

| Field | Value |
| --- | --- |
| Example | `predici_maxwell` - Predici_Maxwell |
| Classification | `montecarlo` / `M42` |
| Status | **PASS** |
| Duration | 0.000436 seconds |
| Metrics | `metric=8.31` |
| Expected | `metric: [0, +inf]` |
| Reason | - |
