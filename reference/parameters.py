"""Literature FRP kinetic parameters. See README.md for sources, DOIs and
verification status of every number here.

Conventions
-----------
Initiation   Ri = 2 * f * kd * [I]              (matches predici_clone)
Termination  literature: -d[R]/dt = 2*<kt>*[R]^2
             predici_clone: -d[R]/dt = kt_code*[R]^2
             => kt_code = 2 * <kt>_literature   (applied by kt_code())
"""
from __future__ import annotations

import numpy as np

R_GAS = 8.314462618  # J mol^-1 K^-1


def _arrhenius(A: float, Ea_J: float, T: float) -> float:
    return A * np.exp(-Ea_J / (R_GAS * T))


# --------------------------------------------------------------- propagation
# IUPAC benchmark kp, REVISED values from the 2022 critical reanalysis
# (DOI 10.1039/d2py00147k, Table 1, read from the open-access full text).
# IUPAC states the revised values replace the earlier per-monomer benchmarks.
# Assume +-8 % on kp and +-1.4 kJ/mol on Ea for any unreplicated PLP study.
KP = {
    # monomer:  A [L/mol/s], Ea [J/mol], validity [K], primary-source DOI
    "styrene": {"A": 10**7.51, "Ea": 31.8e3, "T_range": (261.15, 393.15),
                "doi": "10.1002/macp.1995.021961016"},
    "mma": {"A": 10**6.50, "Ea": 22.8e3, "T_range": (255.15, 365.15),
            "doi": "10.1002/macp.1997.021980518"},
    "ba": {"A": 10**7.22, "Ea": 17.3e3, "T_range": (208.15, 343.15),
           "doi": "10.1002/macp.200400355"},
    "ma": {"A": 10**7.25, "Ea": 17.8e3, "T_range": (247.15, 334.15),
           "doi": "10.1039/c3py00774j"},
    "vac": {"A": 10**7.13, "Ea": 20.4e3, "T_range": (278.15, 343.15),
            "doi": "10.1002/macp.201600357"},
    "bma": {"A": 10**6.57, "Ea": 22.7e3, "T_range": (253.15, 364.15),
            "doi": "10.1002/1521-3935(20000801)201:12<1355::AID-MACP1355>3.0.CO;2-Q"},
}

# Superseded original benchmarks, kept so the revision can be reproduced.
KP_ORIGINAL = {
    "styrene": {"A": 10**7.63, "Ea": 32.5e3},
    "mma": {"A": 10**6.42, "Ea": 22.3e3},
    "ba": {"A": 10**7.34, "Ea": 17.9e3},
    "ma": {"A": 10**7.15, "Ea": 17.3e3},
    "vac": {"A": 10**7.13, "Ea": 20.4e3},
}

# Acrylates propagate via a secondary radical only within the fitted window;
# above it, backbiting produces mid-chain radicals with their own kinetics,
# which predici_clone does not model.
BACKBITING_LIMIT = {"ba": 293.15, "ma": 334.15}   # K


def kp(monomer: str, T: float, *, strict: bool = True) -> float:
    """Propagation rate coefficient [L mol^-1 s^-1]. T in kelvin."""
    p = KP[monomer]
    lo, hi = p["T_range"]
    if strict and not (lo <= T <= hi):
        raise ValueError(
            f"T={T-273.15:.1f} degC is outside the IUPAC validity range for "
            f"{monomer} ({lo-273.15:.0f} to {hi-273.15:.0f} degC)")
    return _arrhenius(p["A"], p["Ea"], T)


def backbiting_warning(monomer: str, T: float) -> str | None:
    """Non-None if the acrylate is being used above its secondary-radical window."""
    limit = BACKBITING_LIMIT.get(monomer)
    if limit is not None and T > limit:
        return (f"{monomer} above {limit-273.15:.0f} degC: benchmark kp covers the "
                f"secondary propagating radical only; backbiting / mid-chain "
                f"radicals are not represented")
    return None


# --------------------------------------------------------------- termination
#
# THERE IS NO IUPAC BENCHMARK kt. The IUPAC task group published only
# diagnostic papers (10.1002/macp.200290041, 10.1016/j.progpolymsci.2005.02.001)
# and no critically-evaluated value exists as of 2026. Every kt below is
# therefore weaker evidence than any kp above, and is labelled accordingly.
#
# Convention: the literature uses -d[R]/dt = 2*<kt>*[R]^2 (verified from the
# equations in DOI 10.1002/pi.6501). predici_clone uses -d[R]/dt = kt*[R]^2,
# hence kt_code = 2 * <kt>_literature, applied by kt_code() below.

# Chain-length-averaged <kt>, low conversion, DILUTE SOLUTION -- NOT bulk.
# 0.67 mol/L monomer in trifluorotoluene/ethylbenzene, AIBN 0.05 M, 50-90 degC.
# DOI 10.3390/polym16223225. <kt> depends on the radical chain-length
# distribution and is NOT transferable to a bulk, differently-initiated system;
# pairing it with a bulk [M] is an acknowledged mismatch.
KT_LIT = {  # T[K] -> <kt> [L mol^-1 s^-1], midpoint of the reported range
    "styrene": {323.15: 3.62e8, 333.15: 3.95e8, 343.15: 6.8e8, 358.15: 8.14e8},
    "mma": {323.15: 8.73e7, 333.15: 9.20e7, 343.15: 1.34e8, 358.15: 3.66e8},
}

# Bulk chain-length-dependent composite model, kt(i,i) = kt11 * i^-alpha_s for
# i <= ic, then i^-alpha_l. SP-PLP-EPR, bulk, -40 degC, <20% conversion.
# DOI 10.1002/macp.201000781 (read from full text).
# NOTE: only kt11 at -40 degC is published; no Arrhenius A/Ea for kt11 was
# verified for any of these monomers, so they cannot be evaluated at reaction
# temperature without an unsupported extrapolation.
KT_COMPOSITE_BULK = {
    "ma": {"kt11": 3.0e8, "alpha_s": 0.80, "alpha_l": 0.25, "ic": 35, "T": 233.15},
    "ba": {"kt11": 9.5e7, "alpha_s": 0.71, "alpha_l": 0.26, "ic": 65, "T": 233.15},
    # exponents only; absolute kt11 could NOT be verified for these two
    "vac": {"kt11": None, "alpha_s": 0.57, "alpha_l": 0.16, "ic": 20, "T": None},
    "bma": {"kt11": None, "alpha_s": 0.65, "alpha_l": 0.20, "ic": 50, "T": None},
}


def kt_literature(monomer: str, T: float) -> float:
    """<kt> in the LITERATURE convention (-d[R]/dt = 2<kt>[R]^2)."""
    if monomer not in KT_LIT:
        raise ValueError(
            f"no tabulated <kt> for {monomer!r}. No IUPAC benchmark kt exists, "
            f"and no bulk Arrhenius kt was verified for this monomer. Supply kt "
            f"explicitly, or sweep it -- see validate_cross_monomer.py.")
    table = KT_LIT[monomer]
    temps = np.array(sorted(table))
    vals = np.array([table[t] for t in temps])
    if not (temps[0] <= T <= temps[-1]):
        raise ValueError(
            f"T={T-273.15:.1f} degC outside the tabulated <kt> range for "
            f"{monomer} ({temps[0]-273.15:.0f} to {temps[-1]-273.15:.0f} degC)")
    return float(np.exp(np.interp(1.0 / T, 1.0 / temps[::-1], np.log(vals[::-1]))))


def kt_code(monomer: str, T: float) -> float:
    """<kt> converted to predici_clone's convention (-d[R]/dt = kt[R]^2)."""
    return 2.0 * kt_literature(monomer, T)


# ------------------------------------------------------------------ initiator
# AIBN. kd from AkzoNobel catalog as tabulated/validated in DOI 10.3390/polym16223225
#       f  from DOI 10.1002/macp.1994.021950620
AIBN = {"kd_A": 2.89e15, "kd_Ea": 130.23e3, "f_A": 5.04, "f_Ea": 5.70e3}


def kd_aibn(T: float) -> float:
    """AIBN decomposition rate coefficient [s^-1]."""
    return _arrhenius(AIBN["kd_A"], AIBN["kd_Ea"], T)


def f_aibn(T: float) -> float:
    """AIBN initiator efficiency [-], for Ri = 2*f*kd*[I]."""
    return _arrhenius(AIBN["f_A"], AIBN["f_Ea"], T)


# --------------------------------------------------------- bulk concentration
# See README section 4 for provenance and verification status of each entry.
MOLAR_MASS = {  # g/mol
    "styrene": 104.15, "mma": 100.12, "ba": 128.17,
    "ma": 86.09, "vac": 86.09, "bma": 142.20,
}
_DENSITY = {  # rho[kg/m3] = a + b*T[degC]
    "styrene": (924.05, -0.8895),
    "mma": (966.35, -1.1483),
    "ba": (919.05, -0.9991),
    "ma": (980.17, -1.2474),
    "vac": (957.06, -1.2558),
    "bma": (914.5, -0.964),
}


def density(monomer: str, T: float) -> float:
    """Liquid density [kg m^-3]. T in kelvin."""
    a, b = _DENSITY[monomer]
    return a + b * (T - 273.15)


def bulk_concentration(monomer: str, T: float) -> float:
    """Neat monomer concentration [mol L^-1]. T in kelvin."""
    return density(monomer, T) / MOLAR_MASS[monomer]


def recipe(monomer: str, T_celsius: float, initiator_molar: float,
           kt_override: float | None = None) -> dict:
    """Assemble a bulk-AIBN recipe in predici_clone's conventions.

    ``kt_override`` is given in predici_clone's convention (-d[R]/dt = kt[R]^2)
    and is required for monomers with no tabulated <kt>.
    """
    T = T_celsius + 273.15
    ktc = kt_override if kt_override is not None else kt_code(monomer, T)
    return {
        "monomer": monomer,
        "T_celsius": T_celsius,
        "kp": kp(monomer, T),
        "kt": ktc,
        "kt_source": "override/sweep" if kt_override is not None else "dilute-solution <kt>",
        "kd": kd_aibn(T),
        "f": f_aibn(T),
        "M0": bulk_concentration(monomer, T),
        "I0": initiator_molar,
        "backbiting": backbiting_warning(monomer, T),
    }


if __name__ == "__main__":
    print("IUPAC revised benchmark kp (DOI 10.1039/d2py00147k) and bulk [M]\n")
    print(f"  {'monomer':<9}{'T(C)':>6}{'kp':>12}{'[M]bulk':>10}"
          f"{'<kt>_lit':>13}{'kt_code':>13}  note")
    for mono in ("styrene", "mma", "ba", "ma", "vac", "bma"):
        for Tc in (50, 60):
            T = Tc + 273.15
            try:
                kp_v = kp(mono, T)
            except ValueError as exc:
                print(f"  {mono:<9}{Tc:>6}  skipped: {exc}")
                continue
            try:
                ktl = f"{kt_literature(mono, T):.3e}"
                ktc = f"{kt_code(mono, T):.3e}"
            except ValueError:
                ktl = ktc = "none"
            note = backbiting_warning(mono, T)
            print(f"  {mono:<9}{Tc:>6}{kp_v:>12.1f}{bulk_concentration(mono, T):>10.3f}"
                  f"{ktl:>13}{ktc:>13}  {'BACKBITING' if note else ''}")
    print(f"\n  AIBN at 60 C: kd={kd_aibn(333.15):.3e} 1/s, f={f_aibn(333.15):.3f}")
    print("  'none' under <kt> means no benchmark or bulk Arrhenius kt was verified.")
