# Reference kinetic parameters — free-radical polymerization

Literature parameters used to validate `predici_clone`'s batch and semi-batch
free-radical polymerization (FRP) engine. Every number below carries its source
DOI and a verification status.

**Verification legend**

| Mark | Meaning |
|---|---|
| ✅ | Read directly from the full text / table retrieved during this work |
| ⚠️ | From an abstract, a secondary source, or extrapolated beyond the fitted range |
| ❌ | Could **not** be verified — **do not use** |

> **Scope note.** These parameters validate that the simulator reproduces
> *textbook FRP behaviour* (kinetic chain length, PDI → 2, the √[I] rate law).
> They are **not** a substitute for comparison against real PREDICI output,
> which remains absent from this project.

---

## 1. Propagation rate coefficient `kp(T)` ✅

**Primary source, read from the open-access full text.** The 2022 IUPAC critical
reanalysis supersedes the individual per-monomer benchmark papers and tabulates
all monomers in one table. IUPAC states explicitly that the revised values
"replace the previously reported values as IUPAC benchmarks", so `parameters.py`
uses the **revised** column.

> Beuermann, S.; Harrisson, S.; Hutchinson, R. A.; Junkers, T.; Russell, G. T.
> *Update and critical reanalysis of IUPAC benchmark propagation rate
> coefficient data.* **Polym. Chem. 2022, 13, 1891–1900.**
> DOI: [10.1039/D2PY00147K](https://doi.org/10.1039/D2PY00147K) ✅ (open access)

```
kp = A * exp(-Ea / RT)         [L mol^-1 s^-1]
```

| Monomer | A (revised) | Ea (kJ mol⁻¹) | kp @ 25 °C | Validity |
|---|---|---|---|---|
| Styrene | 10^7.51 | 31.8 (5) | 87 (2) | −12 to 120 °C |
| MMA | 10^6.50 | 22.8 (4) | 325 (6) | −18 to 92 °C |
| Butyl acrylate (BA) | 10^7.22 | 17.3 (6) | 1.57 × 10⁴ | −65 to 70 °C |
| Methyl acrylate (MA) | 10^7.25 | 17.8 (7) | 1.37 × 10⁴ | −26 to 61 °C |
| Vinyl acetate (VAc) | 10^7.13 | 20.4 (7) | 3.62 × 10³ | 5 to 70 °C |
| Butyl methacrylate (BMA) | 10^6.57 | 22.7 (5) | 390 (11) | −20 to 91 °C |

Parentheses are the standard error in the final digit. **IUPAC's own uncertainty
guidance: assume ±8 % on kp and ±1.4 kJ mol⁻¹ on Ea** for any PLP study without
independent replication.

Note the revision moved styrene's `Ea` by more than 1σ (32.5 → 31.8) — the
originals (`KP_ORIGINAL` in `parameters.py`) are kept so the change is traceable.

⚠️ **Acrylate caveat — confirmed from the full text.** The benchmark `kp` for BA
and MA describes the **secondary propagating radical only**. The fitted datasets
were deliberately truncated ("to avoid interference from backbiting"). Above
roughly 20 °C (BA) / 60 °C (MA), a significant mid-chain-radical population forms
and these values must not be used without an explicit backbiting/MCR model —
which `predici_clone` does not have. `parameters.backbiting_warning()` flags this.
VAc shows no backbiting.

**Primary per-monomer papers** (all DOIs Crossref-verified; full texts returned
402/403 and were **not** opened — the values above come from the 2022 table):

- Styrene: **Macromol. Chem. Phys. 1995, 196, 3267.**
  DOI: [10.1002/macp.1995.021961016](https://doi.org/10.1002/macp.1995.021961016) ⚠️
- MMA: **Macromol. Chem. Phys. 1997, 198, 1545.**
  DOI: [10.1002/macp.1997.021980518](https://doi.org/10.1002/macp.1997.021980518) ⚠️
- BA: Asua et al. **Macromol. Chem. Phys. 2004, 205, 2151.**
  DOI: [10.1002/macp.200400355](https://doi.org/10.1002/macp.200400355) ⚠️
- MA: Barner-Kowollik et al. **Polym. Chem. 2014, 5, 204.**
  DOI: [10.1039/c3py00774j](https://doi.org/10.1039/c3py00774j) ⚠️
- VAc: Barner-Kowollik et al. **Macromol. Chem. Phys. 2017, 218, 1600357.**
  DOI: [10.1002/macp.201600357](https://doi.org/10.1002/macp.201600357) ⚠️
- BMA: Beuermann et al. **Macromol. Chem. Phys. 2000, 201, 1355.**
  DOI: [10.1002/1521-3935(20000801)201:12<1355::AID-MACP1355>3.0.CO;2-Q](https://doi.org/10.1002/1521-3935(20000801)201:12<1355::AID-MACP1355>3.0.CO;2-Q) ⚠️
- Consolidated IUPAC Technical Report: Hutchinson & Beuermann.
  **Pure Appl. Chem. 2019, 91, 1883.**
  DOI: [10.1515/pac-2018-1108](https://doi.org/10.1515/pac-2018-1108) ⚠️

---

## 2. Termination rate coefficient `kt(T)` ⚠️

**Negative result, and it matters.** The IUPAC Task Group on termination
deliberately did **not** issue a benchmark `kt`. Their stated conclusion is that
there is *"large and unacceptable scatter in literature values of kt"* arising
from *"the inherent complexity of the phenomenon of termination"*. Part of that
historical scatter was traced to authors using rate laws differing by a factor
of two. There is therefore **no** `kt` of the same evidential quality as `kp`.

- Buback, M.; Egorov, M.; Gilbert, R. G.; Kaminsky, V.; Olaj, O. F.;
  Russell, G. T.; Vana, P.; Zifferer, G. *Critically evaluated termination rate
  coefficients for free-radical polymerization, 1. The current situation.*
  **Macromol. Chem. Phys. 2002, 203, 2570–2582.**
  DOI: [10.1002/macp.200290041](https://doi.org/10.1002/macp.200290041) ⚠️ (abstract only)

### 2a. Convention — factor of 2 ✅ (now confirmed directly)

The literature uses the IUPAC convention

```
-d[R]/dt = 2 <kt> [R]^2
```

verified from the equations themselves in Buback & Russell,
**Polym. Int. 2023, 72, 869–880**,
DOI: [10.1002/pi.6501](https://doi.org/10.1002/pi.6501) ✅ (open access).
That review also records that historical `kt` scatter was substantially caused
by "rate laws differing by a factor of 2".

`predici_clone` integrates `dR/dt = 2 f kd [I] - kt_code [R]^2`, i.e.

```
-d[R]/dt = kt_code [R]^2
```

Therefore **`kt_code = 2 × <kt>_literature`**, applied by `kt_code()` in
`parameters.py`. The initiation convention `Ri = 2 f kd [I]` already matches.
Do **not** apply the factor a second time.

### 2b. Bulk chain-length-dependent `kt` ✅ — but only two absolute values

Composite model `kt(i,i) = kt(1,1)·i^(−αs)` for `i ≤ ic`, then `i^(−αl)`.
SP-PLP-EPR, **bulk**, −40 °C, < 20 % conversion.

> Barth, J.; Buback, M.; Russell, G. T.; Smolne, S.
> **Macromol. Chem. Phys. 2011, 212, 1366–1378.**
> DOI: [10.1002/macp.201000781](https://doi.org/10.1002/macp.201000781) ✅ (full text)

| Monomer | kt(1,1) | αs | αl | ic |
|---|---|---|---|---|
| MA (bulk) | 3.0 × 10⁸ | 0.80 ± 0.15 | 0.25 ± 0.07 | 35 ± 10 |
| BA (bulk) | 9.5 × 10⁷ | 0.71 ± 0.15 | 0.26 ± 0.07 | 65 ± 20 |
| VAc ⚠️ | **not verified** | 0.57 ± 0.05 | 0.16 ± 0.07 | 20 ± 10 |
| BMA ⚠️ | **not verified** | 0.65 ± 0.10 | 0.20 ± 0.05 | ≈ 50 |

❌ **No Arrhenius A/Ea for `kt(1,1)` was verified for any monomer**, so these
cannot be evaluated at reaction temperature without an unsupported
extrapolation. They are recorded in `parameters.KT_COMPOSITE_BULK` for reference
and are **not used** by the validation scripts.

VAc: Kattner & Buback, **Macromol. Chem. Phys. 2014, 215, 1180.**
DOI: [10.1002/macp.201400095](https://doi.org/10.1002/macp.201400095) ⚠️ (abstract only)
BMA: Barth et al. **Macromolecules 2009, 42, 481.**
DOI: [10.1021/ma802078g](https://doi.org/10.1021/ma802078g) ⚠️ (abstract only)

⚠️ **Acrylates above ~0 °C are a three-termination system** (SPR–SPR, SPR–MCR,
MCR–MCR). A single `⟨kt⟩` is not physically meaningful there at all.

### 2c. Chain-length-averaged `<kt>`, low conversion ⚠️ — the weakest link

⚠️ **These are dilute-solution values, not bulk** (c_M = 0.67 mol L⁻¹,
AIBN c_I = 0.05 mol L⁻¹, conversion < 20 %; ethylbenzene for styrene,
trifluorotoluene for MMA).

⚠️⚠️ **Stronger caveat than first recorded.** `⟨kt⟩` is an average weighted by the
radical chain-length distribution, so it is **not transferable between initiation
regimes**. Pairing a dilute-solution `⟨kt⟩` with a *bulk* `[M]` is not merely
approximate — the two describe different radical populations. This is why the
validation scripts **sweep** `kt` instead of asserting one value: the engine is
required to reproduce theory for *any* parameter set, which is a claim that does
not depend on `kt` being physically right.

| T (°C) | ⟨kt⟩ styrene (L mol⁻¹ s⁻¹) | ⟨kt⟩ MMA (L mol⁻¹ s⁻¹) |
|---|---|---|
| 50 | 3.13–4.11 × 10⁸ | 8.60–8.85 × 10⁷ |
| 60 | 3.95 × 10⁸ | 8.75–9.64 × 10⁷ |
| 70 | 6.8 × 10⁸ | 9.81 × 10⁷ – 1.69 × 10⁸ |
| 85 | 7.51–8.76 × 10⁸ | 1.62–5.70 × 10⁸ |

Activation energies (bulk, long chains, reanalyzed): Ea(⟨kt⟩) ≈ 24 kJ mol⁻¹
(styrene), ≈ 18 kJ mol⁻¹ (MMA).

- Alghamdi, M. M.; Russell, G. T. *On the Activation Energy of Termination in
  Radical Polymerization, as Studied at Low Conversion.*
  **Polymers 2024, 16(22), 3225.**
  DOI: [10.3390/polym16223225](https://doi.org/10.3390/polym16223225) ✅ (open access)

### 2d. Other composite-model data ⚠️

Not used in the validation scripts; recorded for completeness.

- MMA bulk: `kt^{1,1}` = (5.8 ± 1.3) × 10⁸ L mol⁻¹ s⁻¹ at 5 °C;
  Ea ≈ 9 ± 2 kJ mol⁻¹; α ≈ 0.63 ± 0.15. Valid 5–70 °C, i ≤ 100.
  Barth, J.; Buback, M. et al. **Macromol. Rapid Commun. 2009, 30, 1805–1811.**
  DOI: [10.1002/marc.200900335](https://doi.org/10.1002/marc.200900335) ⚠️ (abstract only)
- Styrene bulk: αs = 0.51 ± 0.05, αl = 0.16 ± 0.05, crossover i_c = 30 ± 10;
  Ea(kt^{1,1}) ≈ 9.3 kJ mol⁻¹. Valid 73–135 °C.
  Kattner, H.; Buback, M. **Macromolecules 2015, 48, 309–315.**
  DOI: [10.1021/ma5022665](https://doi.org/10.1021/ma5022665) ⚠️ (abstract only)
  ❌ The numeric `kt^{1,1}` **pre-factor for styrene could not be verified** —
  the abstract states only that it scales as monomer fluidity. Do not assume one.

---

## 3. Initiator: AIBN decomposition `kd(T)` and efficiency `f(T)` ✅

```
kd = 2.89e15 * exp(-130230 / RT)     [s^-1]
f  = 5.04    * exp(-5700   / RT)     [-]
```

| T (°C) | kd (s⁻¹) | half-life | f |
|---|---|---|---|
| 50 | 2.57 × 10⁻⁶ | 75.0 h | 0.604 |
| 60 | 1.10 × 10⁻⁵ | 17.5 h | 0.644 |
| 70 | 4.33 × 10⁻⁵ | 4.45 h | 0.684 |
| 80 | 1.58 × 10⁻⁴ | 1.22 h | 0.723 |

Sanity checks passed: the 10-hour half-life falls between 60–70 °C, matching the
well-known AIBN 10 h half-life temperature of ≈ 65 °C ✅; `f` = 0.60–0.72 lies in
the expected 0.5–0.7 band ✅. `f` is defined for `Ri = 2 f kd [I]`.

⚠️ **Provenance flag.** The `kd` Arrhenius parameters originate from
*AkzoNobel Chemicals, "Initiators for High Polymers" (product catalog), 2006* —
a commercial catalog with **no DOI**. They are, however, explicitly endorsed in
the peer-reviewed literature and are tabulated and validated in
Alghamdi & Russell 2024 (DOI [10.3390/polym16223225](https://doi.org/10.3390/polym16223225)).
Cite them that way, not as a primary peer-reviewed measurement.

The **efficiency** parameters are peer-reviewed ✅:

- Buback, M.; Huckestein, B.; Kuchta, F.-D.; Russell, G. T.; Schmid, E.
  *Initiator efficiencies in 2,2′-azoisobutyronitrile-initiated free-radical
  polymerizations of styrene.* **Macromol. Chem. Phys. 1994, 195(6), 2117–2140.**
  DOI: [10.1002/macp.1994.021950620](https://doi.org/10.1002/macp.1994.021950620) ✅

❌ **Not used — Van Hook & Tobolsky.** The papers are real and their DOIs
resolve (*JACS* 1958, 80, 779, DOI 10.1021/ja01537a006; *J. Polym. Sci.* 1958,
33, 429–445, DOI 10.1002/pol.1958.1203312640), but neither full text was opened
and a circulating "1.58 × 10¹⁵ exp(−30.8 kcal/RT)" figure came from a
non-authoritative aggregator. **Do not use that number.**

### 3a. Other initiators — surveyed, none usable as a complete set

**AIBN remains the only initiator here with both a `kd` and a citable `f`.**

- **tert-Butyl peroxypivalate (TBPP)** ✅ (full text):
  `kd(P,T) = 2.20 × 10¹⁴ · exp{−(14691 + 0.0192·P)/T}` s⁻¹,
  Ea = 122.3 ± 3 kJ mol⁻¹, 65–105 °C, **n-heptane at 0.01 M**, pressure-explicit.
  Buback, M. **Z. Naturforsch. 1984, 39a, 399–411.**
  DOI: [10.1515/zna-1984-0417](https://doi.org/10.1515/zna-1984-0417)
  ❌ but its efficiency has **no obtainable DOI** (see below), so the pair is incomplete.
- **tert-Butyl peroxyacetate (TBPA)** ✅ (full text, open access):
  Ea = 154.28 kJ mol⁻¹, A = 2.12 × 10¹⁷ s⁻¹, **at 2000 bar in squalane**, 393–458 K.
  Albus et al. **J. Solution Chem. 2024, 53, 43–59.**
  DOI: [10.1007/s10953-023-01267-2](https://doi.org/10.1007/s10953-023-01267-2)
  ⚠️ The authors themselves warn that **TBPA does not follow first-order
  decomposition**, and the solvent differs from the usual n-heptane.
- ❌ **Efficiency values f ≈ 1.0 (DTBP), 0.64 (TBPEH), 0.42 (TBPP)** in ethene at
  2000 bar — Becker, Buback, Sandmann, *Macromol. Chem. Phys.* 2002, 203, 2113.
  **No DOI could be obtained. Not cited, not used.**
- ❌ **KPS: nothing verified — no `kd`, no `f`.**
  ❌ **BPO: no A/Ea pair from an opened source, no peer-reviewed `f`.**
  Best target for closing the BPO gap: O'Driscoll & White 1965,
  DOI [10.1002/pol.1965.100030129](https://doi.org/10.1002/pol.1965.100030129)
  (abstract indicates it holds both, for bulk styrene at 90 °C).
- 📌 **Promising lead, not read:** *Kinetic parameters for thermal decomposition
  of commercially available dialkyldiazenes (IUPAC Technical Report)*,
  **Pure Appl. Chem. 2025, 97, 1465–1478**,
  DOI: [10.1515/pac-2024-0252](https://doi.org/10.1515/pac-2024-0252).
  Likely the best-quality source for azo initiators.

> ⚠️ **Anti-fabrication note worth keeping.** Buback et al. 1999,
> *Z. Phys. Chem.* **210**, 199 **has no DOI at all**. A plausible-looking
> constructed identifier (`10.1524/zpch.1999.210.part_2.199`) was tested and
> returns HTTP 404. That is exactly the slot where an invented DOI would pass a
> casual read — treat any DOI for that reference as fabricated.

---

## 4. Bulk monomer concentration

**Molar masses** ✅ (NIST WebBook, read directly):
styrene C₈H₈ = 104.15 g mol⁻¹; MMA C₅H₈O₂ = 100.12 g mol⁻¹.
NIST WebBook carries **no** liquid density for either — it is not cited for density.

⚠️ Both correlations below are **our own least-squares regressions** on
tabulated peer-reviewed data, not published equations. They are presented as such.

### Styrene ✅

```
rho [kg/m3] = 924.05 - 0.8895 * T[degC]        (fitted 20-40 degC)
[M] = rho / 104.15                              [mol/L]
```

Cross-validated to 98.9 °C against an independent source: ρ = 923.94 − 0.9006·T
(U.S. Coast Guard *CHRIS Hazardous Chemical Data Manual*, entry STY, 1999,
<https://cameochemicals.noaa.gov/chris/STY.pdf> ✅, valid 4.4–98.9 °C).
**The two agree within 0.5 kg m⁻³ over 25–80 °C** — a genuine independent check.

| T (°C) | ρ (kg m⁻³) | [M] (mol L⁻¹) |
|---|---|---|
| 25 | 901.8 | 8.659 |
| 50 | 879.6 | 8.445 |
| 60 | 870.7 | 8.360 |
| 70 | 861.8 | 8.275 |
| 80 | 852.9 | 8.189 |

- Wisniak, J. et al. **J. Chem. Thermodyn. 2008, 40, 1671–1683.**
  DOI: [10.1016/j.jct.2008.06.017](https://doi.org/10.1016/j.jct.2008.06.017)
  ⚠️ (DOI verified via CrossRef; density values transcribed from an aggregator,
  primary paper not opened)

### MMA ⚠️ — weaker, use with a stated uncertainty

```
rho [kg/m3] = 966.35 - 1.1483 * T[degC]        (fitted 15-45 degC)
[M] = rho / 100.12                              [mol/L]
```

| T (°C) | ρ (kg m⁻³) | [M] (mol L⁻¹) |
|---|---|---|
| 25 | 937.6 | 9.365 |
| 50 | 908.9 | 9.078 ⚠️ extrapolated |
| 60 | 897.5 | 8.964 ⚠️ extrapolated |
| 70 | 886.0 | 8.849 ⚠️ extrapolated |

⚠️ **Two concerns.** (1) The two available sources disagree by 0.3 % at 25 °C and
their slopes differ by 4 %. (2) Successive density differences in the primary
data are implausibly uniform (5.735 / 5.745 / 5.740 / 5.740 / 5.750 per 5 K),
indicating a single laboratory rather than independent replication.
**Carry ±0.5 % uncertainty on MMA [M] above 50 °C.**

- Nain, A. K. **J. Chem. Thermodyn. 2013, 60, 105–116.**
  DOI: [10.1016/j.jct.2013.01.013](https://doi.org/10.1016/j.jct.2013.01.013) ⚠️
- Droliya, P.; Nain, A. K. **J. Chem. Thermodyn. 2018, 123, 146–157.**
  DOI: [10.1016/j.jct.2018.03.013](https://doi.org/10.1016/j.jct.2018.03.013) ⚠️
- Cross-check: CHRIS manual, entry MMM ✅ (ρ = 967.91 − 1.0991·T, 1.7–48.9 °C)

❌ Patnode & Scheiber, **JACS 1939, 61, 3449–3451**,
DOI 10.1021/ja01267a066 — the canonical primary styrene density paper.
Bibliographic details confirmed, but the paper was **not opened**; no
correlation here is attributed to it.

### Additional monomers

`rho [g/cm3] = a - b*T[degC]`; `[M] = rho(g/L) / MW`.

| Monomer | MW | a | b | Range | [M] @ 50 °C | [M] @ 60 °C |
|---|---|---|---|---|---|---|
| BA | 128.17 | 0.91905 | 9.991e-4 | 5–65 °C | 6.781 | 6.703 |
| MA | 86.09 | 0.98017 | 1.2474e-3 | 5–65 °C | 10.661 | 10.516 |
| VAc | 86.09 | 0.95706 | 1.2558e-3 | 20–40 °C ⚠️ | 10.388 | 10.242 |
| BMA | 142.20 | 0.9145 | 9.64e-4 | not stated ⚠️ | 6.092 | 6.024 |

- **BMA is the best-validated** ✅ — three independent routes agree within 0.06 %.
  Idowu & Hutchinson, **Polymers 2019, 11, 487**,
  DOI: [10.3390/polym11030487](https://doi.org/10.3390/polym11030487)
  (open access, Table 1 read verbatim). No temperature range is stated.
- **BA and MA** ⚠️ — the coefficients are **our own least-squares fits**, not a
  published correlation. Underlying data from Lomba et al.,
  **J. Chem. Eng. Data 2013, 58, 1193**,
  DOI: [10.1021/je301333b](https://doi.org/10.1021/je301333b), read via a
  third-party republication; the ACS paper was **not opened**.
- **VAc** ⚠️ — the fitted range is only 20–40 °C, so 50–60 °C is an
  extrapolation. A DIPPR-105 form (Perry's 8th ed., no DOI; C1=959.1, C2=0.2593,
  C3=519.13, C4=0.27448, valid 180–519 K) needs no extrapolation and gives
  10.393 / 10.085 M at 50 / 70 °C — agreeing with the linear fit to ~0.1 %.
  Prefer the DIPPR form if VAc accuracy matters.

---

## 5. Starved-feed semi-batch — operating envelope ✅

Three cases were verified from open-access full texts. They supply a **realistic
operating envelope** for semi-batch runs, though **not** a numerical
conversion-vs-time / Mn benchmark that could be reproduced point by point.

| Case | Conditions | DOI |
|---|---|---|
| Industrial acrylic resin | 138 °C in xylenes; 239 g monomer fed over **6 h** (≈0.66 g/min); TBPA 2.0 mol% **co-fed**; 65 wt% final polymer; free [M] falls ~0.2 → <0.1 mol/L; branching 7–11 % (vs 2.4–3 % batch) | [10.3390/polym9080368](https://doi.org/10.3390/polym9080368) ✅ |
| **Modelled in PREDICI** | MA + N-tBu-acrylamide, EtOH/H₂O, 60 & 70 °C; feed times **75 / 150 / 225 min**; AIBN 1–2 wt% **precharged**; 10–30 wt% final; starved criterion **unreacted monomer weight fraction < 0.035** | [10.3390/polym15010215](https://doi.org/10.3390/polym15010215) ✅ |
| Emulsion, explicit >90 % | MMA/BA, 70 °C; feed rates **0.5 / 1.0 / 2.0 g/min**; KPS 1 wt% precharged; 50 wt% solids; **instantaneous conversion xi = w_pol/w_mon,added > 0.9 with Rp/Ra ≥ 0.9** | [10.3390/polym15071628](https://doi.org/10.3390/polym15071628) ✅ |

**Envelope used by `validate_cross_monomer.py`:** feed times 75 min – 6 h; feed
rates 0.24–2.0 g/min at 120–380 g scale; 60–70 °C (azo/persulfate) up to 138 °C
(peroxyester); solids 10–65 wt%. Both starved criteria are supported —
instantaneous conversion > 90 %, and free-monomer thresholds (< 0.035 weight
fraction, or [M] < 0.2 mol/L). Initiator policy (precharged vs co-fed) differs by
system and is not incidental.

Notable modelling finding from the PREDICI-modelled case: **primary radical
termination is significant only under starved-feed conditions** — including it
moved 26 of 30 Mw predictions to within 25 % of experiment. `predici_clone` does
not model primary radical termination.

### Still missing ❌

No published case giving **both** conversion-vs-time **and** Mn/PDI as extractable
numbers was obtained — publisher paywalls (402/403) blocked the Hutchinson-group
ACS/Elsevier papers, and no numbers were substituted from them. Classic
candidates (Balke & Hamielec; Hui & Hamielec) were **not** read.

Consequence, stated plainly: everything in `reference/` demonstrates
**consistency with analytical FRP theory**, not agreement with experimental data,
and nothing here compares against real PREDICI output.

---

## 6. Results obtained with these parameters

Run: `python reference/validate_literature.py` (after the `frp_rhs` fix described
in the evaluation report). Reference solutions are method-of-moments, exact and
free of chain-length truncation.

### Units — read this first

`predici_clone` reports `Mn`/`Mw` as **degree of polymerization (chain length in
monomer units)**, not g mol⁻¹. `core/moments.py` builds moments over the array
index; `postprocess/gpc.py` multiplies by `monomer_mw` separately when a real
molar mass is wanted. Molar masses below are our conversion, `DP × M_monomer`.

⚠️ Related defect: `MomentReport.amw` returns `self.mn`, i.e. a chain length
exported under the label **"AMW" (average molecular weight)** via
`api/automation.py`, `postprocess/generic_outputs.py` and `moments_report.py`.
`monomer_mw` is also hardcoded to a generic `100.0` in `gpc.py`, `charting.py`
and `app/main_window.py`.

### Batch and semi-batch, 60 °C, 600 s

| Case | ν (theory) | DP_n (sim) | rel. err | PDI | Mn (g mol⁻¹) | conversion |
|---|---|---|---|---|---|---|
| Styrene batch, [I]₀ = 0.01 M | 269.4 | 270.14 | 0.088 % | 1.990 | 28 100 | 0.273 % |
| MMA batch, [I]₀ = 0.2 M ⚠️ | 308.4 | 309.24 | 0.058 % | 1.992 | 30 960 | 6.02 % |
| Styrene semi-batch, fed | 285.1 | 285.75 | 0.138 % | 1.987 | 29 760 | — |

All quantities (conversion, radical concentration, Mn, Mw, PDI) agree with the
moment reference to better than 0.61 %. Truncation is negligible: the top-bin
occupancy is ≤ 3.5 × 10⁻⁷ at ≥ 8.8× headroom over ν. PDI converges to the
most-probable limit of 2.0 as theory requires.

### Scaling laws — the defining signature of FRP

Styrene bulk, 60 °C, [AIBN] varied 16-fold:

| [I]₀ (mol L⁻¹) | Rp (mol L⁻¹ s⁻¹) | DP_n | PDI |
|---|---|---|---|
| 0.005 | 2.695 × 10⁻⁵ | 378.43 | 1.954 |
| 0.01 | 3.816 × 10⁻⁵ | 270.06 | 1.990 |
| 0.02 | 5.396 × 10⁻⁵ | 191.31 | 1.995 |
| 0.04 | 7.628 × 10⁻⁵ | 135.47 | 1.993 |
| 0.08 | 1.078 × 10⁻⁴ | 95.97 | 1.989 |

```
fitted  d(ln Rp)/d(ln I) = +0.5000     theory +0.5
fitted  d(ln Mn)/d(ln I) = -0.4954     theory -0.5
```

Before the `frp_rhs` fix this test failed completely: DP_n was 1.0005 at every
initiator level, i.e. the simulated chain length did not respond to [I] at all.

### Monomer accounting, semi-batch (mol)

| Term | Value |
|---|---|
| charged + fed | 9.3630494 |
| free monomer (sim) | 9.3395123 |
| bound in **live** chains (sim) | 4.0403 × 10⁻⁶ |
| in **terminated** chains (reference) | 0.0236210 — **not stored by the simulator** |
| closure without dead polymer | 2.5 × 10⁻³ ❌ leaks |
| closure with dead polymer added back | 9.4 × 10⁻⁶ ✅ |

**99.98 % of all polymerised monomer ends up in terminated chains**, which the
simulator discards. The mass-balance line passes only because the reference
supplies the missing term. The product MWD does not exist in the state vector.

### What these results do and do not establish

✅ Establish: with identical parameters, the corrected engine reproduces
analytical FRP theory — kinetic chain length, PDI → 2, and both square-root
initiator laws.

❌ Do **not** establish agreement with experiment. DP ≈ 270 is *shorter* than
real bulk polystyrene (typically DP > 10³) because a **dilute-solution ⟨kt⟩ is
paired with a bulk [M]** — a deliberate, flagged mismatch forced by the absence
of a benchmark bulk `kt` (§2). No published experimental case was verified (§5).

---

## 7. Cross-monomer check with the second literature set

`validate_cross_monomer.py` — **9/9 passed**. Adds BMA and VAc to the styrene/MMA
set and sweeps `kt`, since no benchmark `kt` exists.

| Monomer | T | [I]₀ | kt | ν | DP_n | Mn (g/mol) | PDI | worst err | mass bal |
|---|---|---|---|---|---|---|---|---|---|
| styrene | 60 | 0.01 | 2e8 | 523 | — | — | — | *skipped, grid* | — |
| styrene | 60 | 0.01 | 7.9e8 | 264 | 264.8 | 27,580 | 1.9925 | 0.183 % | 4.6e-4 |
| styrene | 60 | 0.01 | 3e9 | 136 | 136.5 | 14,214 | 1.9890 | 0.185 % | 4.6e-4 |
| MMA | 60 | 0.2 | 1.8e8 | 311 | 321.3 | 32,167 | 1.9928 | 0.233 % | 6.0e-4 |
| MMA | 60 | 0.2 | 1e9 | 138 | 140.9 | 14,103 | 1.9889 | 0.204 % | 5.2e-4 |
| **BMA** | 60 | 0.1 | 2e8 | 349 | 358.6 | 50,993 | 1.9931 | 0.222 % | 5.7e-4 |
| **BMA** | 60 | 0.1 | 1e9 | 161 | 163.2 | 23,211 | 1.9899 | 0.200 % | 5.1e-4 |
| **VAc** | 60 | 0.5 | 5e9 | 384 | 423.4 | 36,452 | 1.9955 | 0.407 % | 1.1e-3 |
| **BMA, combination** | 60 | 0.1 | 1e9 | 161 | 326.6 | 46,446 | **1.4970** | 0.000 % | 5.7e-7 |

The combination row gives `DP_n = 326.6 ≈ 2 × ν`, exactly as fusing two
most-probable chains requires, and PDI → 1.5.

⚠️ The initiator charges and `kt` values above are chosen to keep the chain
length inside the grid budget. **They are not realistic recipes** — see below.

### 7a. A structural limit of the discrete backend ❗

What a *realistic* bulk recipe (AIBN 0.01 M, kt = 2×10⁸) actually demands:

| Monomer | ν | nmax needed (10 ν) |
|---|---|---|
| Styrene | 524 | 5,244 |
| MMA | 1,416 | 14,160 |
| BMA | 1,159 | 11,592 |
| VAc | 16,420 | 164,156 |
| MA | 56,800 | 568,044 |
| **BA** | **513,840** | **5,138,402** |

The discrete backend needs one ODE per chain length — two with dead polymer.
Acrylates propagate roughly 100× faster than methacrylates, so a real bulk
acrylate recipe needs a grid of order 10⁵–10⁶ states. **`predici_clone`'s
discrete backend cannot simulate real acrylate polymerization at all.** This is
precisely why PREDICI uses an adaptive h-p Galerkin discretisation. It is a
property of the backend, unrelated to the propagation fix.

### 7b. Starved-feed semi-batch — engine PASSES, recipe is not starved

Engine agreement is exact (volume, free [M], dead Mn and PDI all within 0.09 %;
mass balance 1.8×10⁻⁵). But the **starved criterion was not reached**: free
monomer stayed at 0.898 mole fraction, not < 0.035.

That is a property of the recipe, not the numerics. With a constant
`kt = 1.85×10⁸` and AIBN at 60 °C the radical flux gives `Rp ≈ 4×10⁻⁶` mol L⁻¹ s⁻¹,
so 75 min consumes only ~0.02 mol L⁻¹; reaching a genuinely starved state would
take days. Real starved-feed runs get there because **`kt` falls by orders of
magnitude as the medium becomes polymer-rich** (diffusion-controlled termination,
the gel effect).

❗ `frp_rhs` uses a **constant `kt`** and never calls
`predici_clone/kinetics/gel_effect.py` — a repo-wide grep finds `apply_gel_effect`
**defined but called from nowhere**. The simulator therefore cannot reproduce
high-solids or starved-feed operation regardless of the fixes applied here.

---

## Running these scripts

| Script | Needs the fix? | Purpose |
|---|---|---|
| `check_engine.py` | **no** — runs on upstream too | Diagnostic. Checks the installed engine against `frp_theory`. On unmodified upstream it reports **0/6** and names the defect; on the corrected code, **6/6**. |
| `frp_theory.py` | no | Analytical moment reference. Imports nothing from `predici_clone`. |
| `parameters.py` | no | Literature parameters; run it to print the table. |
| `validate_literature.py` | **yes** | Styrene/MMA batch + semi-batch, 5/5. |
| `validate_dead_polymer.py` | **yes** | PDI 2.0 / 1.5 limits and mass balance, 4/4. |
| `validate_cross_monomer.py` | **yes** | Second literature set, 9/9. |

The three `validate_*` scripts need `FRPScheme.combination_fraction` and a
reactor `.layout`; on unmodified upstream they will raise. **Start with
`check_engine.py`** — it detects what the build supports and adapts.

```
python reference/check_engine.py
```

## Files

| File | Purpose |
|---|---|
| `README.md` | This bibliography |
| `frp_theory.py` | Analytical FRP moment reference (no repo dependency) |
| `parameters.py` | Literature parameters, with unit/convention conversion |
| `check_engine.py` | Version-agnostic diagnostic |
| `validate_literature.py` | Styrene/MMA batch + semi-batch |
| `validate_dead_polymer.py` | Termination-mode PDI limits + mass balance |
| `validate_cross_monomer.py` | Second literature set + tractability survey |
