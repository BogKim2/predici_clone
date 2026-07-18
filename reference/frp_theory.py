"""Analytical reference for free-radical polymerization — method of moments.

This module has NO dependency on predici_clone. It solves the standard FRP
moment equations exactly (no chain-length truncation) and is the yardstick every
other script here measures the simulator against.

Conventions (matching predici_clone):
    initiation   Ri = 2*f*kd*[I],  primary radicals enter at chain length 1
    termination  -d[R]/dt = kt*[R]^2,  split into
                 ktd = kt*(1-delta)   P_n + P_m -> D_n + D_m
                 ktc = kt*delta       P_n + P_m -> D_(n+m)
    initiation consumes one monomer (R* + M -> RM*)

Live moments  l0,l1,l2;  dead moments  u0,u1,u2.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


def batch(*, kp, kt, kd, f, M0, I0, tend, delta=0.0, rtol=1e-12, atol=1e-24):
    """Exact batch FRP moments. delta = fraction of kt that is combination."""
    ktc, ktd = kt * delta, kt * (1.0 - delta)

    def rhs(_t, y):
        M, I, l0, l1, l2, u0, u1, u2 = y
        M, I, l0 = max(M, 0.0), max(I, 0.0), max(l0, 0.0)
        Ri = 2.0 * f * kd * I
        return [
            -kp * M * l0 - Ri,
            -kd * I,
            Ri - kt * l0 * l0,
            Ri + kp * M * l0 - kt * l0 * l1,
            Ri + kp * M * (2 * l1 + l0) - kt * l0 * l2,
            ktd * l0 * l0 + 0.5 * ktc * l0 * l0,
            ktd * l0 * l1 + ktc * l0 * l1,
            ktd * l0 * l2 + ktc * (l0 * l2 + l1 * l1),
        ]

    s = solve_ivp(rhs, (0.0, tend), [M0, I0, 0, 0, 0, 0, 0, 0],
                  method="BDF", rtol=rtol, atol=atol)
    return _pack(s, M0)


def semibatch(*, kp, kt, kd, f, M0, I0, Mfeed, feed_rate, V0, tend,
              delta=0.0, Ifeed=0.0, rtol=1e-12, atol=1e-24):
    """Exact semi-batch FRP moments with a volumetric feed.

    Concentrations obey dc/dt = R_gen + (F/V)*(c_feed - c) and dV/dt = F.
    """
    ktc, ktd = kt * delta, kt * (1.0 - delta)

    def rhs(_t, y):
        M, I, l0, l1, l2, u0, u1, u2, V = y
        M, I, l0 = max(M, 0.0), max(I, 0.0), max(l0, 0.0)
        V = max(V, 1e-14)
        d = feed_rate / V
        Ri = 2.0 * f * kd * I
        return [
            -kp * M * l0 - Ri + d * (Mfeed - M),
            -kd * I + d * (Ifeed - I),
            Ri - kt * l0 * l0 - d * l0,
            Ri + kp * M * l0 - kt * l0 * l1 - d * l1,
            Ri + kp * M * (2 * l1 + l0) - kt * l0 * l2 - d * l2,
            ktd * l0 * l0 + 0.5 * ktc * l0 * l0 - d * u0,
            ktd * l0 * l1 + ktc * l0 * l1 - d * u1,
            ktd * l0 * l2 + ktc * (l0 * l2 + l1 * l1) - d * u2,
            feed_rate,
        ]

    s = solve_ivp(rhs, (0.0, tend), [M0, I0, 0, 0, 0, 0, 0, 0, V0],
                  method="BDF", rtol=rtol, atol=atol)
    out = _pack(s, M0)
    out["V"] = float(s.y[8, -1])
    # overall monomer accounting, in moles
    out["moles_in"] = M0 * V0 + Mfeed * feed_rate * tend
    out["moles_free"] = out["M"] * out["V"]
    out["moles_bound"] = (out["live_mass"] + out["dead_mass"]) * out["V"]
    return out


def cstr_steady_state(*, kp, kt, kd, f, Mfeed, Ifeed, tau, delta=0.0,
                      tend_factor=60.0, rtol=1e-12, atol=1e-24):
    """CSTR run far past start-up, i.e. effectively the steady state."""
    ktc, ktd = kt * delta, kt * (1.0 - delta)

    def rhs(_t, y):
        M, I, l0, l1, l2, u0, u1, u2 = y
        M, I, l0 = max(M, 0.0), max(I, 0.0), max(l0, 0.0)
        Ri = 2.0 * f * kd * I
        return [
            -kp * M * l0 - Ri + (Mfeed - M) / tau,
            -kd * I + (Ifeed - I) / tau,
            Ri - kt * l0 * l0 - l0 / tau,
            Ri + kp * M * l0 - kt * l0 * l1 - l1 / tau,
            Ri + kp * M * (2 * l1 + l0) - kt * l0 * l2 - l2 / tau,
            ktd * l0 * l0 + 0.5 * ktc * l0 * l0 - u0 / tau,
            ktd * l0 * l1 + ktc * l0 * l1 - u1 / tau,
            ktd * l0 * l2 + ktc * (l0 * l2 + l1 * l1) - u2 / tau,
        ]

    s = solve_ivp(rhs, (0.0, tend_factor * tau), [Mfeed, Ifeed, 0, 0, 0, 0, 0, 0],
                  method="BDF", rtol=rtol, atol=atol)
    return _pack(s, Mfeed)


def _pack(s, M0):
    M, I, l0, l1, l2, u0, u1, u2 = s.y[:8, -1]
    out = {
        "success": bool(s.success), "M": float(M), "I": float(I), "R": float(l0),
        "live_mass": float(l1), "dead_mass": float(u1),
        "conversion": float((M0 - M) / M0),
        "live_Mn": float(l1 / l0) if l0 > 0 else float("nan"),
        "live_Mw": float(l2 / l1) if l1 > 0 else float("nan"),
        "dead_Mn": float(u1 / u0) if u0 > 0 else float("nan"),
        "dead_Mw": float(u2 / u1) if u1 > 0 else float("nan"),
    }
    out["live_PDI"] = out["live_Mw"] / out["live_Mn"] if out["live_Mn"] else float("nan")
    out["dead_PDI"] = out["dead_Mw"] / out["dead_Mn"] if out["dead_Mn"] else float("nan")
    return out


def kinetic_chain_length(*, kp, kt, M, R):
    """nu = kp[M] / (kt[R]) -- the expected number-average degree of polymerization."""
    return kp * M / (kt * R)


def qssa_radical_concentration(*, kt, kd, f, I):
    """Quasi-steady-state radical concentration, sqrt(2 f kd [I] / kt)."""
    return float(np.sqrt(2.0 * f * kd * I / kt))
