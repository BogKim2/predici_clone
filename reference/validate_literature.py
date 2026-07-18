"""Validate predici_clone's batch and semi-batch FRP engine using the
literature parameters in parameters.py (see README.md for DOIs).

Reference solutions are computed by the METHOD OF MOMENTS, which is exact and
free of chain-length truncation. The quantity under test is the repo's own
frp_rhs / BatchReactor / SemiBatchReactor.

Note: the repo's integrate() supplies no jac_sparsity, so SciPy BDF would build
a dense N x N Jacobian and become unusably slow. We call solve_ivp directly with
the correct sparsity pattern. The right-hand side under test is unmodified.
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

import parameters as lit
from predici_clone.core.moments import from_discrete_distribution
from predici_clone.kinetics.reaction import FRPScheme
from predici_clone.kinetics.species import SpeciesState
from predici_clone.reactor.batch import BatchReactor
from predici_clone.reactor.semibatch import SemiBatchReactor

TOL = 0.02  # 2 % agreement required against the moment reference

# The reactors now carry a dead-polymer block, so the live distribution must be
# sliced through the layout rather than a hardcoded y[3:]. Tolerances are also
# tightened: live-radical bins sit at ~1e-9 mol/L, the same order as the
# atol=1e-10 hardcoded in integrator/stepper.py.
RTOL, ATOL = 1e-10, 1e-22


def solve_reactor(rc, tend, *, rtol=RTOL, atol=ATOL, t_eval=None):
    system = rc.system()
    return solve_ivp(system.rhs, (0.0, tend), system.initial_state, method="BDF",
                     rtol=rtol, atol=atol, jac_sparsity=system.jac_sparsity,
                     t_eval=[0.0, tend] if t_eval is None else t_eval)


# ------------------------------------------------------------ batch reference
def batch_moments(p, tend):
    kp, kt, kd, f = p["kp"], p["kt"], p["kd"], p["f"]

    def rhs(t, y):
        M, I, l0, l1, l2, u0, u1, u2 = y
        M, I, l0 = max(M, 0.0), max(I, 0.0), max(l0, 0.0)
        Ri = 2.0 * f * kd * I
        return [-kp * M * l0 - Ri,          # initiation consumes one monomer
                -kd * I,
                Ri - kt * l0 * l0,
                Ri + kp * M * l0 - kt * l0 * l1,
                Ri + kp * M * (2 * l1 + l0) - kt * l0 * l2,
                kt * l0 * l0,               # dead chain count (disproportionation)
                kt * l0 * l1,               # dead mass
                kt * l0 * l2]               # dead second moment
    s = solve_ivp(rhs, (0.0, tend), [p["M0"], p["I0"], 0, 0, 0, 0, 0, 0],
                  method="BDF", rtol=1e-11, atol=1e-22)
    M, I, l0, l1, l2, u0, u1, u2 = s.y[:, -1]
    return {"M": M, "R": l0, "Mn": l1 / l0, "Mw": l2 / l1,
            "PDI": (l2 / l1) / (l1 / l0), "conv": (p["M0"] - M) / p["M0"],
            "live_mass": l1, "dead_mass": u1,
            "dead_Mn": u1 / u0, "dead_Mw": u2 / u1}


def run_batch(title, p, tend, nmax):
    print("\n" + "=" * 78)
    print(f"BATCH  |  {title}")
    print("=" * 78)
    print(f"  {p['monomer']} bulk, {p['T_celsius']:.0f} degC, AIBN [I]0 = {p['I0']:g} mol/L")
    print(f"  kp={p['kp']:.4g}  kt_code={p['kt']:.4g}  kd={p['kd']:.4g}  "
          f"f={p['f']:.4g}  [M]0={p['M0']:.4g}")

    ref = batch_moments(p, tend)
    nu = p["kp"] * ref["M"] / (p["kt"] * ref["R"])
    print(f"  kinetic chain length nu = {nu:.4g}   nmax={nmax} ({nmax/nu:.1f}x headroom)")

    rc = BatchReactor(
        scheme=FRPScheme(kp=p["kp"], kt=p["kt"], kd=p["kd"],
                         initiator_efficiency=p["f"]),
        species=SpeciesState(p["M0"], p["I0"], 0.0), nmax=nmax)
    s = solve_reactor(rc, tend)
    dist = s.y[rc.layout.live, -1]
    dead = s.y[rc.layout.dead, -1]
    sim = from_discrete_distribution(dist, first_length=0)
    dead_rep = from_discrete_distribution(dead, first_length=0)

    rows = [("conversion", ref["conv"], (p["M0"] - s.y[0, -1]) / p["M0"]),
            ("radicals R", ref["R"], dist.sum()),
            ("Mn", ref["Mn"], sim.mn),
            ("Mw", ref["Mw"], sim.mw),
            ("PDI", ref["PDI"], sim.pdi)]
    print(f"\n  {'quantity':<13}{'moment ref':>17}{'predici_clone':>17}{'rel.err':>11}")
    ok = True
    for label, r, v in rows:
        err = abs(v - r) / abs(r)
        ok &= err < TOL
        print(f"  {label:<13}{r:>17.6g}{v:>17.6g}{err:>10.3%} {'OK' if err < TOL else '**'}")

    print(f"\n  chains at length 0 (must be 0): {dist[0]:.3e}")
    print(f"  fraction in top bin            : {dist[-1]/dist.sum():.3e}")
    print(f"  live PDI vs most-probable 2.0  : {sim.pdi:.4f}")

    # product MWD, now tracked
    lengths = np.arange(dist.size, dtype=float)
    consumed = p["M0"] - s.y[0, -1]
    bound = float((dist * lengths).sum() + (dead * lengths).sum())
    err_dead = abs(dead_rep.mn - ref["dead_Mn"]) / ref["dead_Mn"]
    ok &= err_dead < TOL
    print(f"\n  PRODUCT (dead polymer) Mn = {dead_rep.mn:.4f}  "
          f"reference {ref['dead_Mn']:.4f}  err {err_dead:.3%} "
          f"{'OK' if err_dead < TOL else '**'}")
    print(f"  PRODUCT PDI = {dead_rep.pdi:.4f}")
    print(f"  mass balance: consumed {consumed:.6g} vs bound {bound:.6g}  "
          f"err {abs(consumed-bound)/consumed:.3e}")
    print(f"  --> {'PASS' if ok else 'MISMATCH'}")
    return ok


# ------------------------------------------------------- semi-batch reference
def semibatch_moments(p, tend, Mfeed, F, V0):
    kp, kt, kd, f = p["kp"], p["kt"], p["kd"], p["f"]

    def rhs(t, y):
        M, I, l0, l1, l2, u1, V = y
        M, I, l0 = max(M, 0.0), max(I, 0.0), max(l0, 0.0)
        V = max(V, 1e-14)
        d = F / V
        Ri = 2.0 * f * kd * I
        return [-kp * M * l0 - Ri + d * (Mfeed - M),
                -kd * I + d * (0.0 - I),
                Ri - kt * l0 * l0 - d * l0,
                Ri + kp * M * l0 - kt * l0 * l1 - d * l1,
                Ri + kp * M * (2 * l1 + l0) - kt * l0 * l2 - d * l2,
                kt * l0 * l1 - d * u1,
                F]
    s = solve_ivp(rhs, (0.0, tend), [p["M0"], p["I0"], 0, 0, 0, 0, V0],
                  method="BDF", rtol=1e-11, atol=1e-22)
    M, I, l0, l1, l2, u1, V = s.y[:, -1]
    return {"M": M, "R": l0, "Mn": l1 / l0, "Mw": l2 / l1,
            "PDI": (l2 / l1) / (l1 / l0), "V": V,
            "live_mass": l1, "dead_mass": u1}


def run_semibatch(title, p, tend, nmax, Mfeed, F, V0):
    print("\n" + "=" * 78)
    print(f"SEMI-BATCH  |  {title}")
    print("=" * 78)
    print(f"  {p['monomer']} bulk, {p['T_celsius']:.0f} degC, AIBN [I]0 = {p['I0']:g} mol/L")
    print(f"  feed {F:g} L/s of {Mfeed:.4g} mol/L monomer into V0={V0:g} L for {tend:g} s")

    ref = semibatch_moments(p, tend, Mfeed, F, V0)
    nu = p["kp"] * ref["M"] / (p["kt"] * ref["R"])
    print(f"  kinetic chain length nu = {nu:.4g}   nmax={nmax} ({nmax/nu:.1f}x headroom)")

    rc = SemiBatchReactor(
        scheme=FRPScheme(kp=p["kp"], kt=p["kt"], kd=p["kd"],
                         initiator_efficiency=p["f"]),
        species=SpeciesState(p["M0"], p["I0"], 0.0), nmax=nmax, volume=V0,
        feed_rate=F, feed_species=SpeciesState(Mfeed, 0.0, 0.0))
    s = solve_reactor(rc, tend)
    dist = s.y[rc.layout.live, -1]
    dead = s.y[rc.layout.dead, -1]
    sim = from_discrete_distribution(dist, first_length=0)
    V = s.y[-1, -1]

    rows = [("volume", ref["V"], V),
            ("monomer [M]", ref["M"], s.y[0, -1]),
            ("radicals R", ref["R"], dist.sum()),
            ("Mn", ref["Mn"], sim.mn),
            ("Mw", ref["Mw"], sim.mw),
            ("PDI", ref["PDI"], sim.pdi)]
    print(f"\n  {'quantity':<13}{'moment ref':>17}{'predici_clone':>17}{'rel.err':>11}")
    ok = True
    for label, r, v in rows:
        err = abs(v - r) / abs(r)
        ok &= err < TOL
        print(f"  {label:<13}{r:>17.6g}{v:>17.6g}{err:>10.3%} {'OK' if err < TOL else '**'}")

    # Overall monomer accounting, in MOLES (volume changes).
    lengths = np.arange(dist.size, dtype=float)
    fed = Mfeed * F * tend
    moles_in = p["M0"] * V0 + fed
    free = s.y[0, -1] * V
    live = float((dist * lengths).sum()) * V
    dead_moles = float((dead * lengths).sum()) * V
    dead_rep = from_discrete_distribution(dead, first_length=0)
    print(f"\n  monomer accounting [mol]")
    print(f"    charged + fed               = {moles_in:.8g}")
    print(f"    free monomer (sim)          = {free:.8g}")
    print(f"    bound in LIVE chains (sim)  = {live:.8g}")
    print(f"    bound in DEAD chains (sim)  = {dead_moles:.8g}")
    err_full = abs(moles_in - free - live - dead_moles) / moles_in
    print(f"    MASS BALANCE closure        = {err_full:.3e}  {'OK' if err_full < 1e-3 else '**'}")
    print(f"  PRODUCT Mn = {dead_rep.mn:.4f}   PDI = {dead_rep.pdi:.4f}")
    print(f"  --> {'PASS' if ok else 'MISMATCH'} (moment agreement)")
    return ok, err_full < 1e-3


# --------------------------------------------------- classic FRP scaling laws
def scaling_law(p_base, tend, nmax, initiators):
    """Rp ~ [I]^0.5 and Mn ~ [I]^-0.5 -- the defining signature of FRP."""
    print("\n" + "=" * 78)
    print("SCALING LAWS  |  styrene bulk 60 degC, varying [AIBN]")
    print("=" * 78)
    print("  Textbook: Rp proportional to [I]^0.5,  Mn proportional to [I]^-0.5")
    print(f"\n  {'[I]0':>9}{'Rp (mol/L/s)':>16}{'Mn':>12}{'PDI':>9}")
    data = []
    for I0 in initiators:
        p = dict(p_base, I0=I0)
        rc = BatchReactor(
            scheme=FRPScheme(kp=p["kp"], kt=p["kt"], kd=p["kd"],
                             initiator_efficiency=p["f"]),
            species=SpeciesState(p["M0"], I0, 0.0), nmax=nmax)
        s = solve_reactor(rc, tend)
        rep = from_discrete_distribution(s.y[rc.layout.dead, -1], first_length=0)
        Rp = (p["M0"] - s.y[0, -1]) / tend
        data.append((I0, Rp, rep.mn))
        print(f"  {I0:>9.4g}{Rp:>16.6g}{rep.mn:>12.4f}{rep.pdi:>9.4f}")

    I = np.array([d[0] for d in data])
    Rp = np.array([d[1] for d in data])
    Mn = np.array([d[2] for d in data])
    slope_rp = np.polyfit(np.log(I), np.log(Rp), 1)[0]
    slope_mn = np.polyfit(np.log(I), np.log(Mn), 1)[0]
    print(f"\n  fitted d(ln Rp)/d(ln I) = {slope_rp:+.4f}   (theory +0.5)")
    print(f"  fitted d(ln Mn)/d(ln I) = {slope_mn:+.4f}   (theory -0.5)")
    ok = abs(slope_rp - 0.5) < 0.02 and abs(slope_mn + 0.5) < 0.02
    print(f"  --> {'PASS' if ok else 'MISMATCH'}")
    return ok


if __name__ == "__main__":
    results = {}

    # nmax is chosen to give ~9x or more headroom over the kinetic chain
    # length; the reported top-bin fraction confirms truncation is negligible.
    sty60 = lit.recipe("styrene", 60.0, 0.01)
    results["batch styrene 60C"] = run_batch(
        "styrene bulk / AIBN, 60 degC", sty60, tend=600.0, nmax=2500)

    # MMA needs a high initiator charge to keep the kinetic chain length inside
    # a tractable nmax; flagged as an unusually concentrated recipe.
    mma60 = lit.recipe("mma", 60.0, 0.2)
    results["batch MMA 60C"] = run_batch(
        "MMA bulk / AIBN, 60 degC (high [I] for tractable nmax)",
        mma60, tend=600.0, nmax=3000)

    ok_mom, ok_bal = run_semibatch(
        "styrene bulk / AIBN, 60 degC, monomer-fed", sty60,
        tend=600.0, nmax=2500, Mfeed=lit.bulk_concentration("styrene", 333.15),
        F=2.0e-4, V0=1.0)
    results["semibatch moments"] = ok_mom
    results["semibatch mass balance"] = ok_bal

    results["scaling laws"] = scaling_law(
        sty60, tend=300.0, nmax=2500,
        initiators=(0.005, 0.01, 0.02, 0.04, 0.08))

    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for k, v in results.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\n  {sum(results.values())}/{len(results)} checks passed")
