"""Cross-check the FRP engine against a SECOND, independent literature set.

The first validation (validate_literature.py) used styrene and MMA. This one
adds butyl acrylate, methyl acrylate, vinyl acetate and butyl methacrylate from
the 2022 IUPAC critical reanalysis (DOI 10.1039/d2py00147k), and sweeps kt --
because no benchmark kt exists for any monomer, so no single value can be
claimed as "the" literature one.

Three parts:
  A. Tractability survey -- what kinetic chain length does each real bulk
     recipe actually produce, and can the discrete backend represent it?
  B. Engine validation for the tractable monomers, against frp_theory.
  C. Starved-feed semi-batch, following the published operating envelope.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
if (HERE.parent / "predici_clone" / "__init__.py").exists():
    sys.path.insert(1, str(HERE.parent))

import numpy as np
from scipy.integrate import solve_ivp

import frp_theory as theory
import parameters as lit
from predici_clone.core.moments import from_discrete_distribution
from predici_clone.kinetics.reaction import FRPScheme
from predici_clone.kinetics.species import SpeciesState
from predici_clone.reactor.batch import BatchReactor
from predici_clone.reactor.semibatch import SemiBatchReactor

TOL = 0.02
# Tight enough that live-radical bins (~1e-9 mol/L) keep their significant
# figures, loose enough to finish: atol=1e-22 on a 7000-state semi-batch run
# was measured at >9 CPU-hours without converging.
RTOL, ATOL = 1e-8, 1e-18
NMAX_BUDGET = 4000       # largest chain grid we are willing to integrate


def solve_reactor(rc, tend, *, rtol=RTOL, atol=ATOL):
    system = rc.system()
    return solve_ivp(system.rhs, (0.0, tend), system.initial_state, method="BDF",
                     rtol=rtol, atol=atol, jac_sparsity=system.jac_sparsity,
                     t_eval=[0.0, tend])


def banner(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


# ------------------------------------------------------- A. tractability
def tractability_survey():
    banner("A. TRACTABILITY  what chain length does each real bulk recipe give?")
    print("  Bulk monomer, AIBN 0.01 mol/L, kt fixed at 2e8 (order-of-magnitude")
    print("  stand-in -- no benchmark kt exists). nu = kp[M]/(kt[R]).")
    print(f"\n  {'monomer':<9}{'T(C)':>5}{'kp':>10}{'[M]':>8}{'nu':>12}"
          f"{'nmax needed':>14}  verdict")
    kt, I0 = 2.0e8, 0.01
    rows = []
    for mono, Tc in (("styrene", 60), ("mma", 60), ("bma", 60),
                     ("vac", 60), ("ma", 60), ("ba", 20)):
        T = Tc + 273.15
        kp_v = lit.kp(mono, T)
        M = lit.bulk_concentration(mono, T)
        R = theory.qssa_radical_concentration(kt=kt, kd=lit.kd_aibn(T),
                                              f=lit.f_aibn(T), I=I0)
        nu = theory.kinetic_chain_length(kp=kp_v, kt=kt, M=M, R=R)
        needed = int(10 * nu)
        ok = needed <= NMAX_BUDGET
        rows.append((mono, Tc, nu, ok))
        print(f"  {mono:<9}{Tc:>5}{kp_v:>10.0f}{M:>8.2f}{nu:>12.4g}{needed:>14,}"
              f"  {'within budget' if ok else 'over budget'}")
    print("\n  The discrete backend needs one ODE per chain length (x2 with dead")
    print("  polymer). Acrylates propagate ~100x faster than methacrylates, so a")
    print("  real bulk acrylate recipe needs a grid of order 1e5-1e6 -- which is")
    print("  precisely why PREDICI uses an h-p Galerkin discretisation rather than")
    print("  a discrete one. This is a limitation of the backend, not of the fix.")
    return rows


# ------------------------------------------------------- B. engine validation
HEADROOM = 10        # nmax must exceed the kinetic chain length by this factor


def validate_monomer(mono, Tc, I0, kt, nmax=None, delta=0.0, tend=600.0):
    """Validate one case. nmax is sized from the kinetic chain length; a case
    needing more grid than NMAX_BUDGET is SKIPPED, not failed -- an
    under-resolved grid measures truncation, not the rate equations."""
    T = Tc + 273.15
    p = dict(kp=lit.kp(mono, T), kt=kt, kd=lit.kd_aibn(T), f=lit.f_aibn(T),
             M0=lit.bulk_concentration(mono, T), I0=I0)
    ref = theory.batch(**p, tend=tend, delta=delta)
    nu = theory.kinetic_chain_length(kp=p["kp"], kt=kt, M=ref["M"], R=ref["R"])
    warn = lit.backbiting_warning(mono, T)

    need = int(np.ceil(HEADROOM * nu * (2 if delta > 0 else 1)))
    if nmax is None:
        nmax = need
    if need > NMAX_BUDGET:
        print(f"  {mono:<8}{Tc:>4}{I0:>7.3g}{kt:>10.2g}{nu:>9.1f}{'-':>7}"
              f"{'':>10}{'':>11}{'':>8}{'':>9}{'':>10}  SKIP (needs nmax "
              f"{need:,} > budget {NMAX_BUDGET:,})")
        return None

    rc = BatchReactor(
        scheme=FRPScheme(kp=p["kp"], kt=kt, kd=p["kd"],
                         initiator_efficiency=p["f"], combination_fraction=delta),
        species=SpeciesState(p["M0"], I0, 0.0), nmax=nmax)
    s = solve_reactor(rc, tend)
    live = s.y[rc.layout.live, -1]
    dead = s.y[rc.layout.dead, -1]
    live_rep = from_discrete_distribution(live, first_length=0)
    dead_rep = from_discrete_distribution(dead, first_length=0)

    lengths = np.arange(live.size, dtype=float)
    consumed = p["M0"] - s.y[0, -1]
    bound = float((live * lengths).sum() + (dead * lengths).sum())
    bal = abs(consumed - bound) / consumed if consumed else float("nan")

    checks = [("conversion", ref["conversion"], (p["M0"] - s.y[0, -1]) / p["M0"]),
              ("live Mn", ref["live_Mn"], live_rep.mn),
              ("dead Mn", ref["dead_Mn"], dead_rep.mn),
              ("dead PDI", ref["dead_PDI"], dead_rep.pdi)]
    worst = max(abs(v - r) / abs(r) for _, r, v in checks)
    ok = worst < TOL and bal < 2e-3

    mw = lit.MOLAR_MASS[mono]
    print(f"  {mono:<8}{Tc:>4}{I0:>7.3g}{kt:>10.2g}{nu:>9.1f}{nmax:>7}"
          f"{dead_rep.mn:>10.2f}{dead_rep.mn*mw:>11,.0f}{dead_rep.pdi:>8.4f}"
          f"{worst:>9.3%}{bal:>10.1e}  {'OK' if ok else '**'}")
    if warn:
        print(f"           ^ {warn}")
    return ok


def engine_validation():
    banner("B. ENGINE VALIDATION  tractable monomers vs the moment reference")
    print("  kt has no benchmark value, so it is swept: the point is that the")
    print("  engine reproduces theory for ANY parameter set, not that a particular")
    print("  kt is right. Mn(g/mol) = DP x monomer molar mass.")
    print(f"  nmax is sized at {HEADROOM}x the kinetic chain length; cases needing")
    print(f"  more than {NMAX_BUDGET:,} bins are skipped rather than run under-resolved.")
    print(f"\n  {'mono':<8}{'T':>4}{'[I]0':>7}{'kt':>10}{'nu':>9}{'nmax':>7}"
          f"{'DP_n':>10}{'Mn g/mol':>11}{'PDI':>8}{'worst':>9}{'massbal':>10}")
    results = []
    # styrene: dilute-solution <kt> and a sweep around it
    for kt in (2.0e8, 7.9e8, 3.0e9):
        results.append(validate_monomer("styrene", 60, 0.01, kt))
    # MMA, high initiator charge to shorten the chains
    for kt in (1.84e8, 1.0e9):
        results.append(validate_monomer("mma", 60, 0.2, kt))
    # butyl methacrylate: the new monomer from the 2022 reanalysis
    for kt in (2.0e8, 1.0e9):
        results.append(validate_monomer("bma", 60, 0.1, kt))
    # vinyl acetate, also new, at a high kt to stay inside the grid budget
    results.append(validate_monomer("vac", 60, 0.5, 5.0e9))
    # termination mode varied on a new monomer: pure combination
    results.append(validate_monomer("bma", 60, 0.1, 1.0e9, delta=1.0))
    print("\n  last row is pure combination (PDI -> 1.5); all others "
          "disproportionation (PDI -> 2.0)")
    print("  NOTE: initiator charges and kt values here are chosen to keep the")
    print("  chain length inside the grid budget. They are NOT realistic recipes;")
    print("  part A shows what a realistic recipe would demand.")
    return [r for r in results if r is not None]


# ------------------------------------------------------- C. starved feed
def starved_feed():
    banner("C. STARVED-FEED SEMI-BATCH")
    print("  Operating envelope from the published starved-feed literature:")
    print("    feed times 75 min - 6 h, initiator precharged or co-fed,")
    print("    starved criterion: unreacted monomer weight fraction < 0.035")
    print("    DOI 10.3390/polym15010215 (modelled in PREDICI), 10.3390/polym9080368")
    print("  Monomer substituted to BMA: the published MA/BA cases give nu ~ 1e5,")
    print("  which the discrete backend cannot represent (see part A).")

    Tc, T = 60, 333.15
    feed_minutes = 75.0                 # shortest published feed time
    tend = feed_minutes * 60.0
    kt = 1.85e8                         # order-of-magnitude stand-in; no benchmark kt
    kp_v = lit.kp("bma", T)
    Mbulk = lit.bulk_concentration("bma", T)
    M0, I0 = 0.10, 0.01                 # starved initial charge, initiator precharged
    V0, F = 1.0, 2.0e-6                 # neat monomer fed slowly

    ref = theory.semibatch(kp=kp_v, kt=kt, kd=lit.kd_aibn(T), f=lit.f_aibn(T),
                           M0=M0, I0=I0, Mfeed=Mbulk, feed_rate=F, V0=V0, tend=tend)

    # Size the grid from the kinetic chain length. An oversized grid is not
    # merely wasteful: a long tail of ~1e-200 bins makes the stiff solver crawl.
    nu = theory.kinetic_chain_length(kp=kp_v, kt=kt, M=ref["M"], R=ref["R"])
    nmax = max(200, int(np.ceil(HEADROOM * nu)))
    print(f"\n  kinetic chain length nu = {nu:.1f} -> nmax = {nmax}")
    rc = SemiBatchReactor(
        scheme=FRPScheme(kp=kp_v, kt=kt, kd=lit.kd_aibn(T),
                         initiator_efficiency=lit.f_aibn(T)),
        species=SpeciesState(M0, I0, 0.0), nmax=nmax, volume=V0,
        feed_rate=F, feed_species=SpeciesState(Mbulk, 0.0, 0.0))
    s = solve_reactor(rc, tend)
    if not s.success:
        print(f"  solver FAILED: {s.message}")
        return False

    live = s.y[rc.layout.live, -1]
    dead = s.y[rc.layout.dead, -1]
    V = s.y[-1, -1]
    lengths = np.arange(live.size, dtype=float)
    dead_rep = from_discrete_distribution(dead, first_length=0)

    moles_in = M0 * V0 + Mbulk * F * tend
    free = s.y[0, -1] * V
    bound = float((live * lengths).sum() + (dead * lengths).sum()) * V
    bal = abs(moles_in - free - bound) / moles_in
    inst_conv = bound / moles_in
    free_frac = free / moles_in

    rows = [("volume", ref["V"], V),
            ("free [M]", ref["M"], s.y[0, -1]),
            ("dead Mn", ref["dead_Mn"], dead_rep.mn),
            ("dead PDI", ref["dead_PDI"], dead_rep.pdi)]
    print(f"\n  BMA, {Tc} degC, AIBN {I0} M precharged, feed {feed_minutes:.0f} min")
    print(f"  {'quantity':<12}{'moment ref':>16}{'predici_clone':>16}{'rel.err':>11}")
    ok = True
    for label, r, v in rows:
        err = abs(v - r) / abs(r)
        ok &= err < TOL
        print(f"  {label:<12}{r:>16.6g}{v:>16.6g}{err:>10.3%} "
              f"{'OK' if err < TOL else '**'}")

    print(f"\n  monomer charged + fed  = {moles_in:.6g} mol")
    print(f"  converted to polymer   = {bound:.6g} mol  "
          f"(instantaneous conversion {inst_conv:.2%})")
    print(f"  unreacted free monomer = {free_frac:.4f} mole fraction")
    print(f"  mass balance closure   = {bal:.3e}  {'OK' if bal < 2e-3 else '**'}")
    print(f"  product Mn = {dead_rep.mn*lit.MOLAR_MASS['bma']:,.0f} g/mol, "
          f"PDI = {dead_rep.pdi:.4f}")
    ok &= bal < 2e-3
    print(f"  --> {'PASS' if ok else 'FAIL'}  (engine agreement + mass balance)")

    # Reported as an observation, NOT as a pass/fail of the engine: the starved
    # criterion is a property of the recipe, not of the numerics.
    starved = free_frac < 0.035
    print(f"\n  starved criterion (free monomer < 0.035): "
          f"{'MET' if starved else 'NOT met'} ({free_frac:.3f})")
    if not starved:
        print("  Why: with a constant kt of 1.85e8 and AIBN at 60 degC, the radical")
        print("  flux gives Rp ~ 4e-6 mol/L/s, so 75 min consumes only ~0.02 mol/L.")
        print("  Reaching a genuinely starved state at this Rp would take days.")
        print("  Real starved-feed runs get there because kt falls by orders of")
        print("  magnitude as the medium becomes polymer-rich (diffusion-controlled")
        print("  termination / gel effect). predici_clone's frp_rhs uses a CONSTANT")
        print("  kt and never calls kinetics/gel_effect.py, so it cannot reproduce")
        print("  high-solids starved-feed operation regardless of this fix.")
    return ok


if __name__ == "__main__":
    tractability_survey()
    batch_results = engine_validation()
    sf = starved_feed()

    banner("SUMMARY")
    print(f"  batch cross-monomer : {sum(batch_results)}/{len(batch_results)} passed")
    print(f"  starved-feed semi-batch : {'PASS' if sf else 'FAIL'}")
    total = sum(batch_results) + (1 if sf else 0)
    n = len(batch_results) + 1
    print(f"\n  {total}/{n} checks passed")
    raise SystemExit(0 if total == n else 1)
