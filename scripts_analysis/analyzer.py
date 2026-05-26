from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from scripts_analysis.coffin_manson import FailureRisk, lifetime_estimate
from scripts_analysis.data_loader import load_json_report
from scripts_analysis.visualization import (
    plot_damage_accumulation,
    plot_degradation_curve,
    plot_woehler_diagram,
)


@dataclass
class AnalysisResult:
    simulation_id: str
    estimated_total_cycles: int
    risk: FailureRisk
    plot_paths: list[str] = field(default_factory=list)
    miner_total_damage: float = 0.0


def run_analysis(
    report_path: str | Path,
    output_dir: str | Path = ".",
) -> AnalysisResult:
    """Load JSON report → fatigue model → visualizations → AnalysisResult."""
    report_path = Path(report_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if report_path.suffix.lower() != ".json":
        raise NotImplementedError("CSV-only analysis requires MaterialProperties — use JSON.")

    report = load_json_report(report_path)
    cycles = report.thermal_cycles
    mat = report.material_properties
    sim_id = report.simulation_id

    lifetime = lifetime_estimate(cycles, mat)
    total_damage = sum(lifetime["miner_damage_per_cycle"])
    strain_values = sorted({c.plastic_strain_range for c in cycles})

    plots = [
        plot_degradation_curve(cycles, mat,
            output_path=output_dir / f"{sim_id}_degradation.png"),
        plot_woehler_diagram(strain_values, mat,
            output_path=output_dir / f"{sim_id}_woehler.png"),
        plot_damage_accumulation(lifetime["miner_damage_per_cycle"],
            output_path=output_dir / f"{sim_id}_damage.png"),
    ]

    return AnalysisResult(
        simulation_id=sim_id,
        estimated_total_cycles=lifetime["estimated_total_cycles"],
        risk=lifetime["risk"],
        plot_paths=plots,
        miner_total_damage=total_damage,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="IBM HPC Thermal Fatigue Analyzer — Coffin-Manson / Miner pipeline"
    )
    parser.add_argument("report", help="Path to thermal simulation report (.json)")
    parser.add_argument("--output-dir", default="simulations/results",
                        help="Output directory for plots (default: simulations/results)")
    args = parser.parse_args()

    result = run_analysis(args.report, output_dir=args.output_dir)
    print("\n=== Analysis Complete ===")
    print(f"Simulation ID    : {result.simulation_id}")
    print(f"Estimated life   : {result.estimated_total_cycles:,} cycles")
    print(f"Cumulative damage: {result.miner_total_damage:.6f}")
    print(f"Risk level       : {result.risk.value}")
    print(f"\nPlots saved to   : {args.output_dir}")
    for p in result.plot_paths:
        print(f"  -> {p}")

    sys.exit(0 if result.risk.value in ("LOW", "MODERATE") else 1)
