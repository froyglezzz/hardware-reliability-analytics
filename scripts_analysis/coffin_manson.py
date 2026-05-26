from __future__ import annotations

import math
from enum import Enum

from scripts_analysis.data_loader import MaterialProperties, ThermalCycle


class FailureRisk(Enum):
    LOW      = "LOW"       # D < 0.25
    MODERATE = "MODERATE"  # 0.25 <= D < 0.5
    HIGH     = "HIGH"      # 0.5  <= D < 0.8
    CRITICAL = "CRITICAL"  # D    >= 0.8


def cycles_to_failure(cycle: ThermalCycle, mat: MaterialProperties) -> float:
    """Coffin-Manson: Nf = 0.5 * (delta_ep / ef_prime) ^ (1/c)."""
    if cycle.plastic_strain_range <= 0:
        raise ValueError("plastic_strain_range must be positive")
    ratio = cycle.plastic_strain_range / mat.fatigue_ductility_coefficient
    return 0.5 * (ratio ** (1.0 / mat.fatigue_ductility_exponent))


def engelmaier_exponent(T_mean_C: float, freq_cycles_per_day: float) -> float:
    """Engelmaier (1983) temperature- and frequency-dependent fatigue exponent.

    c = -0.442 - 6e-4*Tm + 1.74e-2*ln(1 + f)
    """
    if freq_cycles_per_day <= 0:
        raise ValueError("freq_cycles_per_day must be positive")
    return -0.442 - 6e-4 * T_mean_C + 1.74e-2 * math.log(1.0 + freq_cycles_per_day)


def miner_damage(
    cycle_count_pairs: list[tuple[ThermalCycle, float]],
    mat: MaterialProperties,
) -> float:
    """Miner's rule: D = sum(n_i / Nf_i).

    Args:
        cycle_count_pairs: (cycle, applied_count) — how many times each cycle was applied.
        mat: Material properties used to compute Nf_i.
    """
    return sum(
        n / cycles_to_failure(c, mat)
        for c, n in cycle_count_pairs
        if n > 0
    )


def lifetime_estimate(cycles: list[ThermalCycle], mat: MaterialProperties) -> dict:
    """Compute per-type Nf, cumulative Miner damage, and failure risk.

    Returns dict with keys:
        cycles_to_failure_per_cycle_type: dict[cycle_id -> Nf]
        miner_damage_per_cycle: list of per-application damage fractions
        estimated_total_cycles: int — cycles until D reaches 1.0
        risk: FailureRisk
    """
    nf_cache: dict[int, float] = {}
    per_cycle: list[float] = []
    total_damage = 0.0

    for cycle in cycles:
        nf = nf_cache.setdefault(cycle.cycle_id, cycles_to_failure(cycle, mat))
        dmg = 1.0 / nf
        per_cycle.append(dmg)
        total_damage += dmg

    estimated_total = int(round(len(cycles) / total_damage)) if total_damage > 0 else int(1e9)

    if total_damage >= 0.8:
        risk = FailureRisk.CRITICAL
    elif total_damage >= 0.5:
        risk = FailureRisk.HIGH
    elif total_damage >= 0.25:
        risk = FailureRisk.MODERATE
    else:
        risk = FailureRisk.LOW

    return {
        "cycles_to_failure_per_cycle_type": nf_cache,
        "miner_damage_per_cycle": per_cycle,
        "estimated_total_cycles": estimated_total,
        "risk": risk,
    }
