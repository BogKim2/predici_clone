"""Diagnostic: check predici_clone's FRP engine against analytical theory.

Runs against WHATEVER version of predici_clone is importable, and is designed to
work on the unmodified upstream code as well as on a corrected one. Nothing here
is self-referential: every expected value comes from `frp_theory.py`, which is
pure scipy and knows nothing about predici_clone.

    python reference/check_engine.py

Each check prints its own PASS/FAIL and, on failure, the size and direction of
the discrepancy. Exit code is 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# Add the repo root only if it really holds the package, so a same-named parent
# directory cannot shadow it.
if (HERE.parent / "predici_clone" / "__init__.py").exists():
    sys.path.insert(1, str(HERE.parent))

import numpy as np

import frp_theory as theory
import parameters as lit

try:
    from predici_clone.core.moments import from_discrete_distribution
    from predici_clone.kinetics.rate_terms import frp_rhs
    from predici_clone.kinetics.reaction import FRPScheme
    from predici_clone.kinetics.species import SpeciesState
    from predici_clone.reactor.batch import BatchReactor
    from predici_clone.reactor.semibatch import SemiBatchReactor
except ImportError as exc:  # pragma: no cover
    print(f"Cannot import predici_clone: {exc}")
    print("Run this from the repository root, or install the package first.")
    raise SystemExit(2)

from scipy.integrate import solve_ivp


# --------------------------------------------------------------- capabilities
def capabilities() -> dict:
    """What does the installed predici_clone actually support?"""
    caps = {
        "combination_fraction": "combination_fraction" in FRPScheme.__dataclass_fields__,
        "layout": hasattr(BatchReactor, "layout"),
    }
    caps["dead_polymer"] = caps["layout"]
    return caps


CAPS = capabilities()


def make_scheme(kp, kt, kd, f, delta=0.0):
    if CAPS["combination_fraction"]:
        return FRPScheme(kp=kp, kt=kt, kd=kd, initiator_efficiency=f,
                         combination_fraction=delta)
    if delta:
        raise RuntimeError("this build has no combination_fraction")
    return FRPScheme(kp=kp, kt=kt, kd=kd, initiator_efficiency=f)


def split_state(reactor, y_final):
    """Return (live, dead) distributions, whichever layout this build uses."""
    if CAPS["layout"]:
        layout = reactor.layout
        live = y_final[layout.live]
        dead = y_final[layout.dead] if layout.track_dead else None
        return live, dead
    # legacy: live chains only, volume (semi-batch) trailing
    tail = -1 if isinstance(reactor, SemiBatchReactor) else None
    return y_final[3:tail], None


def integrate(reactor, tend, rtol=1e-10, atol=1e-22):
    system = reactor.system()
    sparsity = getattr(system, "jac_sparsity", None)
    kw = {"jac_sparsity": sparsity} if sparsity is not None else {}
    return solve_ivp(system.rhs, (0.0, tend), system.initial_state, method="BDF",
                     rtol=rtol, atol=atol, t_eval=[0.0, tend], **kw)


def banner(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def verdict(ok, note=""):
    print(f"  --> {'PASS' if ok else 'FAIL'}{('  ' + note) if note else ''}")
    return ok


# ------------------------------------------------------------------- checks
def check_propagation_rate_law():
    """Probe the RHS directly: d(P_4)/dt must equal kp*M*P_3."""
    banner("CHECK 1  propagation rate law")
    nmax = 12
    scheme = make_scheme(1000.0, 1.0e7, 1.0e-5, 0.5)
    M, P3 = 5.0, 2.0e-7
    if CAPS["layout"]:
        from predici_clone.kinetics.rate_terms import FRPStateLayout
        layout = FRPStateLayout(nmax=nmax, track_dead=True)
        y = np.zeros(layout.size)
        y[0], y[1], y[2] = M, 0.01, P3
        y[layout.live.start + 3] = P3
        d = frp_rhs(0.0, y, scheme, layout)
        got = d[layout.live.start + 4]
    else:
        y = np.zeros(nmax + 4)
        y[0], y[1], y[2] = M, 0.01, P3
        y[3 + 3] = P3
        d = frp_rhs(0.0, y, scheme)
        got = d[3 + 4]

    want = scheme.kp * M * P3
    ratio = got / want
    print(f"  kp*M*P_3 (theory)      = {want:.6g}")
    print(f"  d(P_4)/dt from frp_rhs = {got:.6g}")
    print(f"  ratio                  = {ratio:.6g}   (must be 1.0)")
    if abs(ratio - 1.0) > 1e-6:
        print(f"  NOTE: the ratio equals the radical concentration R = {P3:.3g}.")
        print(f"        The propagation coefficient carries an extra factor of R:")
        print(f"        `propagation = kp * monomer * radicals` should be `kp * monomer`.")
    return verdict(abs(ratio - 1.0) < 1e-6)


def check_zero_length_radicals():
    banner("CHECK 2  primary radicals must enter at chain length 1, not 0")
    scheme = make_scheme(100.0, 1.0e7, 1.0e-5, 0.5)
    rc = BatchReactor(scheme=scheme, species=SpeciesState(5.0, 1.0, 0.0), nmax=400)
    s = integrate(rc, 100.0)
    live, _ = split_state(rc, s.y[:, -1])
    frac = live[0] / live.sum() if live.sum() else float("nan")
    print(f"  population at chain length 0 = {live[0]:.6g}  ({frac:.4%} of all chains)")
    if frac > 1e-6:
        print("  NOTE: chains of length zero are unphysical and drag the reported")
        print("        Mn below 1.0, which cannot happen for a real polymer.")
    return verdict(frac < 1e-6)


def check_chain_length_and_pdi():
    banner("CHECK 3  Mn matches the kinetic chain length, PDI approaches 2")
    p = dict(kp=100.0, kt=1.0e7, kd=1.0e-5, f=0.5, M0=5.0, I0=1.0, tend=200.0)
    ref = theory.batch(**p, delta=0.0)
    nu = theory.kinetic_chain_length(kp=p["kp"], kt=p["kt"], M=ref["M"], R=ref["R"])
    rc = BatchReactor(scheme=make_scheme(p["kp"], p["kt"], p["kd"], p["f"]),
                      species=SpeciesState(p["M0"], p["I0"], 0.0), nmax=800)
    s = integrate(rc, p["tend"])
    live, dead = split_state(rc, s.y[:, -1])
    live_rep = from_discrete_distribution(live, first_length=0)

    print(f"  kinetic chain length nu   = {nu:.4f}")
    print(f"  live Mn  theory {ref['live_Mn']:>10.4f}   simulated {live_rep.mn:>10.4f}")
    ok = abs(live_rep.mn - ref["live_Mn"]) / ref["live_Mn"] < 0.02
    print(f"  live PDI theory {ref['live_PDI']:>10.4f}   simulated {live_rep.pdi:>10.4f}")
    if dead is not None:
        dead_rep = from_discrete_distribution(dead, first_length=0)
        print(f"  dead Mn  theory {ref['dead_Mn']:>10.4f}   simulated {dead_rep.mn:>10.4f}")
        print(f"  dead PDI theory {ref['dead_PDI']:>10.4f}   simulated {dead_rep.pdi:>10.4f}"
              f"   (analytical limit 2.0)")
        ok &= abs(dead_rep.mn - ref["dead_Mn"]) / ref["dead_Mn"] < 0.02
    if not ok:
        print(f"  NOTE: a simulated Mn near 1.0 means chains are not growing at all.")
    return verdict(ok)


def check_mass_balance():
    banner("CHECK 4  monomer mass balance")
    p = dict(kp=100.0, kt=1.0e7, kd=1.0e-5, f=0.5, M0=5.0, I0=1.0, tend=200.0)
    rc = BatchReactor(scheme=make_scheme(p["kp"], p["kt"], p["kd"], p["f"]),
                      species=SpeciesState(p["M0"], p["I0"], 0.0), nmax=800)
    s = integrate(rc, p["tend"])
    live, dead = split_state(rc, s.y[:, -1])
    lengths = np.arange(live.size, dtype=float)
    consumed = p["M0"] - s.y[0, -1]
    bound = float((live * lengths).sum())
    if dead is not None:
        bound += float((dead * lengths).sum())
    err = abs(consumed - bound) / consumed if consumed else float("nan")
    print(f"  monomer consumed        = {consumed:.8g} mol/L")
    print(f"  bound in polymer chains = {bound:.8g} mol/L")
    print(f"  closure error           = {err:.3e}")
    if dead is None:
        ref = theory.batch(**p, delta=0.0)
        print(f"  NOTE: this build has no dead-polymer state. Terminated chains are")
        print(f"        discarded, so {ref['dead_mass']/(ref['dead_mass']+ref['live_mass']):.2%} "
              f"of all polymerised monomer disappears")
        print(f"        and the product MWD is never computed.")
    return verdict(err < 1e-3)


def check_initiator_scaling():
    banner("CHECK 5  square-root initiator laws (the signature of FRP)")
    p = dict(kp=100.0, kt=1.0e7, kd=1.0e-5, f=0.5, M0=5.0, tend=200.0)
    initiators = (0.25, 0.5, 1.0, 2.0, 4.0)
    print(f"  {'[I]0':>8}{'Rp':>16}{'Mn':>12}")
    rows = []
    for I0 in initiators:
        rc = BatchReactor(scheme=make_scheme(p["kp"], p["kt"], p["kd"], p["f"]),
                          species=SpeciesState(p["M0"], I0, 0.0), nmax=800)
        s = integrate(rc, p["tend"])
        live, dead = split_state(rc, s.y[:, -1])
        rep = from_discrete_distribution(dead if dead is not None else live,
                                         first_length=0)
        Rp = (p["M0"] - s.y[0, -1]) / p["tend"]
        rows.append((I0, Rp, rep.mn))
        print(f"  {I0:>8.4g}{Rp:>16.6g}{rep.mn:>12.4f}")
    I = np.array([r[0] for r in rows])
    slope_rp = np.polyfit(np.log(I), np.log([r[1] for r in rows]), 1)[0]
    slope_mn = np.polyfit(np.log(I), np.log([r[2] for r in rows]), 1)[0]
    print(f"\n  d(ln Rp)/d(ln I) = {slope_rp:+.4f}   (theory +0.5)")
    print(f"  d(ln Mn)/d(ln I) = {slope_mn:+.4f}   (theory -0.5)")
    ok = abs(slope_rp - 0.5) < 0.03 and abs(slope_mn + 0.5) < 0.03
    if not ok:
        print("  NOTE: if Mn does not move with initiator at all, chain growth is")
        print("        not coupled to the radical population.")
    return verdict(ok)


def check_semibatch():
    banner("CHECK 6  semi-batch: dilution and overall monomer accounting")
    p = dict(kp=100.0, kt=1.0e7, kd=1.0e-5, f=0.5, M0=5.0, I0=1.0, tend=200.0)
    Mfeed, F, V0 = 8.0, 0.002, 1.0
    ref = theory.semibatch(**p, Mfeed=Mfeed, feed_rate=F, V0=V0, delta=0.0)
    rc = SemiBatchReactor(scheme=make_scheme(p["kp"], p["kt"], p["kd"], p["f"]),
                          species=SpeciesState(p["M0"], p["I0"], 0.0), nmax=800,
                          volume=V0, feed_rate=F,
                          feed_species=SpeciesState(Mfeed, 0.0, 0.0))
    s = integrate(rc, p["tend"])
    if not s.success:
        print(f"  solver FAILED: {s.message}")
        return verdict(False)
    live, dead = split_state(rc, s.y[:, -1])
    V = s.y[-1, -1]
    lengths = np.arange(live.size, dtype=float)
    moles_in = p["M0"] * V0 + Mfeed * F * p["tend"]
    free = s.y[0, -1] * V
    bound = float((live * lengths).sum()) * V
    if dead is not None:
        bound += float((dead * lengths).sum()) * V
    err = abs(moles_in - free - bound) / moles_in
    print(f"  volume    theory {ref['V']:>10.6f}   simulated {V:>10.6f}")
    print(f"  [M] final theory {ref['M']:>10.6f}   simulated {s.y[0,-1]:>10.6f}")
    print(f"  monomer charged + fed = {moles_in:.8g} mol")
    print(f"  free + bound          = {free + bound:.8g} mol")
    print(f"  closure error         = {err:.3e}")

    # A mass balance closes trivially when nothing polymerises, so require the
    # run to have actually produced polymer before crediting the closure.
    expected_bound = ref["moles_bound"]
    print(f"  polymer formed: theory {expected_bound:.6g} mol, "
          f"simulated {bound:.6g} mol")
    if bound < 0.01 * expected_bound:
        print("  NOTE: essentially no polymer was formed, so the mass balance closes")
        print("        vacuously. Treated as a failure, not a pass.")
        return verdict(False)

    ok = (abs(V - ref["V"]) / ref["V"] < 1e-6
          and err < 1e-3
          and abs(s.y[0, -1] - ref["M"]) / ref["M"] < 0.02)
    return verdict(ok)


def main():
    print("=" * 78)
    print("predici_clone FRP engine — analytical check")
    print("=" * 78)
    print(f"  dead-polymer tracking : {'yes' if CAPS['dead_polymer'] else 'NO'}")
    print(f"  ktd/ktc split         : {'yes' if CAPS['combination_fraction'] else 'NO'}")
    if not CAPS["dead_polymer"]:
        print("\n  This build has no dead-polymer state, so checks 4 and 6 measure the")
        print("  live chains only and are expected to show a large mass leak.")

    checks = [check_propagation_rate_law, check_zero_length_radicals,
              check_chain_length_and_pdi, check_mass_balance,
              check_initiator_scaling, check_semibatch]
    results = {}
    for fn in checks:
        try:
            results[fn.__name__] = fn()
        except Exception as exc:
            banner(f"{fn.__name__} raised")
            print(f"  {type(exc).__name__}: {exc}")
            results[fn.__name__] = False

    banner("SUMMARY")
    for name, ok in results.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    passed = sum(results.values())
    print(f"\n  {passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
