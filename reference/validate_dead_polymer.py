"""Validate the dead-polymer (product MWD) implementation.

Three independent checks, none self-referential:

  1. PDI of the product -> 2.0 for pure disproportionation,
                        -> 1.5 for pure combination.
     These are exact analytical limits of the most-probable distribution and
     its self-convolution.
  2. Full moment agreement against a truncation-free method-of-moments
     reference for live AND dead chains.
  3. Monomer mass balance closes: M consumed == sum(n * (P_n + D_n)).
     Before dead-polymer tracking this leaked ~100 % of the polymerised mass.
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

from predici_clone.core.moments import from_discrete_distribution
from predici_clone.kinetics.reaction import FRPScheme
from predici_clone.kinetics.species import SpeciesState
from predici_clone.reactor.batch import BatchReactor
from predici_clone.reactor.semibatch import SemiBatchReactor

TOL = 0.02

# predici_clone's integrate() hardcodes rtol=1e-7, atol=1e-10. Live-radical bin
# populations are of order 1e-9 mol/L, i.e. the same size as that atol, so the
# live distribution is integrated at essentially no significant figures. The
# dead distribution accumulates to much larger values and is unaffected. We
# therefore drive the reactor's own system with a tolerance appropriate to the
# state magnitudes; see the note in the summary.
RTOL, ATOL = 1e-10, 1e-22


def solve_reactor(rc, tend, *, rtol=RTOL, atol=ATOL, trailing=0):
    """Integrate a reactor's own system with explicit tolerances."""
    system = rc.system()
    return solve_ivp(system.rhs, (0.0, tend), system.initial_state, method="BDF",
                     rtol=rtol, atol=atol, jac_sparsity=system.jac_sparsity,
                     t_eval=[0.0, tend])


def moment_reference(kp, kt, kd, f, delta, M0, I0, tend):
    """Exact live and dead moments. delta = combination fraction of kt."""
    ktc, ktd = kt * delta, kt * (1.0 - delta)

    def rhs(t, y):
        M, I, l0, l1, l2, u0, u1, u2 = y
        M, I, l0 = max(M, 0.0), max(I, 0.0), max(l0, 0.0)
        Ri = 2.0 * f * kd * I
        return [
            -kp * M * l0 - Ri,                              # initiation eats a monomer
            -kd * I,
            Ri - kt * l0 * l0,
            Ri + kp * M * l0 - kt * l0 * l1,
            Ri + kp * M * (2 * l1 + l0) - kt * l0 * l2,
            ktd * l0 * l0 + 0.5 * ktc * l0 * l0,            # dead chain count
            ktd * l0 * l1 + ktc * l0 * l1,                  # dead mass
            ktd * l0 * l2 + ktc * (l0 * l2 + l1 * l1),      # dead second moment
        ]

    s = solve_ivp(rhs, (0.0, tend), [M0, I0, 0, 0, 0, 0, 0, 0],
                  method="BDF", rtol=1e-12, atol=1e-24)
    M, I, l0, l1, l2, u0, u1, u2 = s.y[:, -1]
    return {"M": M, "R": l0, "live_Mn": l1 / l0, "live_mass": l1,
            "dead_Mn": u1 / u0, "dead_Mw": u2 / u1, "dead_PDI": (u2 / u1) / (u1 / u0),
            "dead_mass": u1, "conv": (M0 - M) / M0}


def run(title, *, kp, kt, kd, f, delta, M0, I0, tend, nmax, pdi_target):
    print("\n" + "=" * 78)
    print(f"{title}")
    print("=" * 78)
    print(f"  combination_fraction = {delta:.2f}   "
          f"(ktd={kt*(1-delta):.4g}, ktc={kt*delta:.4g})")

    ref = moment_reference(kp, kt, kd, f, delta, M0, I0, tend)
    nu = kp * ref["M"] / (kt * ref["R"])
    print(f"  kinetic chain length nu = {nu:.4g}   nmax={nmax} "
          f"({nmax/nu:.1f}x headroom; combination needs 2x more)")

    rc = BatchReactor(
        scheme=FRPScheme(kp=kp, kt=kt, kd=kd, initiator_efficiency=f,
                         combination_fraction=delta),
        species=SpeciesState(M0, I0, 0.0), nmax=nmax)
    s = solve_reactor(rc, tend)
    layout = rc.layout
    live = s.y[layout.live, -1]
    dead = s.y[layout.dead, -1]
    live_rep = from_discrete_distribution(live, first_length=0)
    dead_rep = from_discrete_distribution(dead, first_length=0)

    rows = [("conversion", ref["conv"], (M0 - s.y[0, -1]) / M0),
            ("radicals R", ref["R"], live.sum()),
            ("live Mn", ref["live_Mn"], live_rep.mn),
            ("dead Mn", ref["dead_Mn"], dead_rep.mn),
            ("dead Mw", ref["dead_Mw"], dead_rep.mw),
            ("dead PDI", ref["dead_PDI"], dead_rep.pdi)]
    print(f"\n  {'quantity':<13}{'moment ref':>17}{'predici_clone':>17}{'rel.err':>11}")
    ok = True
    for label, r, v in rows:
        err = abs(v - r) / abs(r)
        ok &= err < TOL
        print(f"  {label:<13}{r:>17.6g}{v:>17.6g}{err:>10.3%} {'OK' if err < TOL else '**'}")

    # analytical PDI limit (only the pure channels have a simple closed form;
    # a mixture of the two does not average linearly, so it is checked against
    # the moment reference alone)
    if pdi_target is None:
        pdi_ok = True
        print(f"\n  product PDI = {dead_rep.pdi:.4f}   (no simple closed form for a "
              f"mixture; checked against the moment reference above)")
    else:
        pdi_err = abs(dead_rep.pdi - pdi_target) / pdi_target
        pdi_ok = pdi_err < 0.03
        print(f"\n  product PDI = {dead_rep.pdi:.4f}   analytical limit = {pdi_target:.2f}"
              f"   dev {pdi_err:.2%}  {'OK' if pdi_ok else '**'}")

    # mass balance
    lengths = np.arange(live.size, dtype=float)
    consumed = M0 - s.y[0, -1]
    bound = float((live * lengths).sum() + (dead * lengths).sum())
    bal = abs(consumed - bound) / consumed
    bal_ok = bal < 1e-3
    print(f"  monomer consumed = {consumed:.8g}   bound in polymer = {bound:.8g}")
    print(f"  mass balance error = {bal:.3e}  {'OK' if bal_ok else '**'}")
    print(f"  dead / total polymerised mass = "
          f"{(dead*lengths).sum()/bound:.4%}   (was 0 % before: chains were discarded)")
    print(f"  top-bin occupancy: live {live[-1]/live.sum():.2e}, "
          f"dead {dead[-1]/dead.sum():.2e}")
    verdict = ok and pdi_ok and bal_ok
    print(f"  --> {'PASS' if verdict else 'FAIL'}")
    return verdict


def run_semibatch(title, *, kp, kt, kd, f, delta, M0, I0, Mfeed, F, V0, tend, nmax):
    print("\n" + "=" * 78)
    print(f"{title}")
    print("=" * 78)
    rc = SemiBatchReactor(
        scheme=FRPScheme(kp=kp, kt=kt, kd=kd, initiator_efficiency=f,
                         combination_fraction=delta),
        species=SpeciesState(M0, I0, 0.0), nmax=nmax, volume=V0,
        feed_rate=F, feed_species=SpeciesState(Mfeed, 0.0, 0.0))
    s = solve_reactor(rc, tend)
    layout = rc.layout
    live = s.y[layout.live, -1]
    dead = s.y[layout.dead, -1]
    V = s.y[-1, -1]
    lengths = np.arange(live.size, dtype=float)
    dead_rep = from_discrete_distribution(dead, first_length=0)

    moles_in = M0 * V0 + Mfeed * F * tend
    free = s.y[0, -1] * V
    bound = float((live * lengths).sum() + (dead * lengths).sum()) * V
    bal = abs(moles_in - free - bound) / moles_in
    print(f"  solver success = {s.success}   ({s.message})")
    print(f"  feed {F:g} L/s of {Mfeed:g} mol/L for {tend:g} s; V {V0:g} -> {V:.4g} L")
    print(f"  monomer charged + fed = {moles_in:.8g} mol")
    print(f"  free monomer          = {free:.8g} mol")
    print(f"  bound in live + dead  = {bound:.8g} mol")
    print(f"  MASS BALANCE error    = {bal:.3e}  {'OK' if bal < 1e-3 else '**'}")
    print(f"  product Mn = {dead_rep.mn:.4f}  PDI = {dead_rep.pdi:.4f}")
    print(f"  --> {'PASS' if bal < 1e-3 else 'FAIL'}")
    return bal < 1e-3


if __name__ == "__main__":
    base = dict(kp=100.0, kt=1.0e7, kd=1.0e-5, f=0.5, M0=5.0, I0=1.0, tend=200.0)
    results = {}

    results["disproportionation -> PDI 2.0"] = run(
        "PURE DISPROPORTIONATION  (combination_fraction = 0)",
        **base, delta=0.0, nmax=800, pdi_target=2.0)

    results["combination -> PDI 1.5"] = run(
        "PURE COMBINATION  (combination_fraction = 1)",
        **base, delta=1.0, nmax=1200, pdi_target=1.5)

    results["mixed 50/50"] = run(
        "MIXED  (combination_fraction = 0.5)",
        **base, delta=0.5, nmax=1200, pdi_target=None)

    results["semi-batch mass balance"] = run_semibatch(
        "SEMI-BATCH mass balance, monomer-fed",
        kp=100.0, kt=1.0e7, kd=1.0e-5, f=0.5, delta=0.0, M0=5.0, I0=1.0,
        Mfeed=8.0, F=0.002, V0=1.0, tend=200.0, nmax=800)

    # ---------------------------------------------------------------- caveat
    print("\n" + "=" * 78)
    print("SOLVER TOLERANCE CAVEAT (not a formulation error)")
    print("=" * 78)
    ref = moment_reference(**base, delta=0.0)
    rc = BatchReactor(
        scheme=FRPScheme(kp=base["kp"], kt=base["kt"], kd=base["kd"],
                         initiator_efficiency=base["f"], combination_fraction=0.0),
        species=SpeciesState(base["M0"], base["I0"], 0.0), nmax=800)
    print(f"  {'tolerances':<28}{'live Mn':>12}{'err':>10}{'dead Mn':>12}{'err':>10}")
    for label, rtol, atol in (("repo default 1e-7 / 1e-10", 1e-7, 1e-10),
                              ("tightened 1e-10 / 1e-22", 1e-10, 1e-22)):
        s = solve_reactor(rc, base["tend"], rtol=rtol, atol=atol)
        lv = from_discrete_distribution(s.y[rc.layout.live, -1], first_length=0).mn
        dd = from_discrete_distribution(s.y[rc.layout.dead, -1], first_length=0).mn
        print(f"  {label:<28}{lv:>12.4f}{abs(lv-ref['live_Mn'])/ref['live_Mn']:>9.2%}"
              f"{dd:>12.4f}{abs(dd-ref['dead_Mn'])/ref['dead_Mn']:>9.2%}")
    print("  Live-radical bins hold ~1e-9 mol/L, the same order as the hardcoded")
    print("  atol=1e-10 in integrator/stepper.py, so the LIVE distribution loses")
    print("  its significant figures. The DEAD distribution accumulates to much")
    print("  larger values and is accurate at either tolerance.")

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\n  {sum(results.values())}/{len(results)} checks passed")
