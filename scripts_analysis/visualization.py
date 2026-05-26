from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from scripts_analysis.coffin_manson import cycles_to_failure
from scripts_analysis.data_loader import MaterialProperties, ThermalCycle

_DARK = {
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#161b22",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "text.color": "#c9d1d9",
    "grid.color": "#21262d",
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
    "lines.linewidth": 2.0,
}


def _style() -> None:
    plt.rcParams.update(_DARK)


def plot_degradation_curve(
    cycles: list[ThermalCycle],
    mat: MaterialProperties,
    output_path: str | Path = "degradation_curve.png",
    title: str = "Solder Joint Degradation — Cumulative Miner Damage",
) -> str:
    """Cumulative Miner's damage vs. thermal cycle number."""
    _style()
    nf_cache: dict[int, float] = {}
    cum: list[float] = []
    total = 0.0
    for cycle in cycles:
        nf = nf_cache.setdefault(cycle.cycle_id, cycles_to_failure(cycle, mat))
        total += 1.0 / nf
        cum.append(total)

    x = list(range(1, len(cum) + 1))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(x, cum, color="#58a6ff", marker="o", markersize=4, label="Cumulative Damage D")
    ax.axhline(1.0, color="#f85149", ls="--", lw=1.5, label="Failure threshold (D=1)")
    ax.axhline(0.8, color="#e3b341", ls=":",  lw=1.2, label="Critical threshold (D=0.8)")
    ax.set_xlabel("Thermal Cycle #")
    ax.set_ylabel("Miner's Damage Index D")
    ax.set_title(title, fontsize=13, fontweight="bold", color="#f0f6fc")
    ax.legend(framealpha=0.3, edgecolor="#30363d")
    ax.grid(True)
    plt.tight_layout()
    out = str(output_path)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_woehler_diagram(
    strain_range_values: list[float],
    mat: MaterialProperties,
    output_path: str | Path = "woehler_diagram.png",
    title: str = "Wöhler S-N Diagram — SAC305 (Coffin-Manson)",
) -> str:
    """Log-log S-N diagram: plastic strain range vs. cycles to failure."""
    if not strain_range_values:
        raise ValueError("strain_range_values must not be empty")
    _style()

    nf_pts = [cycles_to_failure(ThermalCycle(0, -40, 125, 10, 10, s), mat)
              for s in strain_range_values]
    sr_fine = np.logspace(
        math.log10(min(strain_range_values) * 0.5),
        math.log10(max(strain_range_values) * 2.0),
        300,
    )
    nf_fine = [cycles_to_failure(ThermalCycle(0, -40, 125, 10, 10, float(s)), mat)
               for s in sr_fine]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.loglog(nf_fine, sr_fine, color="#58a6ff", lw=2, label="Coffin-Manson fit")
    ax.scatter(nf_pts, strain_range_values, color="#3fb950", zorder=5,
               s=60, label="Simulation data points")
    ax.set_xlabel("Cycles to Failure Nf")
    ax.set_ylabel("Plastic Strain Range Δεp")
    ax.set_title(title, fontsize=13, fontweight="bold", color="#f0f6fc")
    ax.legend(framealpha=0.3, edgecolor="#30363d")
    ax.grid(True, which="both")
    plt.tight_layout()
    out = str(output_path)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_damage_accumulation(
    damage_sequence: list[float],
    output_path: str | Path = "damage_accumulation.png",
    title: str = "Incremental Damage per Thermal Cycle",
) -> str:
    """Bar chart of per-cycle damage fraction."""
    if not damage_sequence:
        raise ValueError("damage_sequence must not be empty")
    _style()

    x = list(range(1, len(damage_sequence) + 1))
    colors = ["#f85149" if d > 0.01 else "#3fb950" for d in damage_sequence]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(x, damage_sequence, color=colors, edgecolor="#21262d", lw=0.5)
    ax.set_xlabel("Cycle #")
    ax.set_ylabel("Damage Fraction 1/Nf")
    ax.set_title(title, fontsize=13, fontweight="bold", color="#f0f6fc")
    ax.yaxis.set_major_formatter(mticker.ScalarFormatter(useMathText=True))
    ax.grid(True, axis="y")
    plt.tight_layout()
    out = str(output_path)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out
