from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

REQUIRED_CSV_COLUMNS = {
    "cycle_id", "T_min_C", "T_max_C",
    "ramp_rate_C_per_min", "dwell_min_min", "plastic_strain_range",
}


@dataclass(frozen=True)
class ThermalCycle:
    cycle_id: int
    T_min_C: float
    T_max_C: float
    ramp_rate_C_per_min: float
    dwell_min_min: float
    plastic_strain_range: float

    @property
    def delta_T(self) -> float:
        return self.T_max_C - self.T_min_C

    @property
    def T_mean_C(self) -> float:
        return (self.T_max_C + self.T_min_C) / 2.0


@dataclass(frozen=True)
class MaterialProperties:
    elastic_modulus_GPa: float
    poissons_ratio: float
    CTE_ppm_per_C: float
    substrate_CTE_ppm_per_C: float
    fatigue_ductility_coefficient: float  # εf'
    fatigue_ductility_exponent: float     # c  (typically −0.5 to −0.7)
    shear_modulus_GPa: float

    @property
    def CTE_mismatch_ppm(self) -> float:
        return abs(self.CTE_ppm_per_C - self.substrate_CTE_ppm_per_C)


@dataclass
class SimulationReport:
    simulation_id: str
    component: str
    material: str
    material_properties: MaterialProperties
    thermal_cycles: list[ThermalCycle]
    fea_solver: str
    mesh_elements: int
    convergence_criterion: float
    geometry: dict = field(default_factory=dict)


def load_json_report(path: str | Path) -> SimulationReport:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation report not found: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    mp = raw["material_properties"]
    mat = MaterialProperties(
        elastic_modulus_GPa=mp["elastic_modulus_GPa"],
        poissons_ratio=mp["poissons_ratio"],
        CTE_ppm_per_C=mp["CTE_ppm_per_C"],
        substrate_CTE_ppm_per_C=mp["substrate_CTE_ppm_per_C"],
        fatigue_ductility_coefficient=mp["fatigue_ductility_coefficient"],
        fatigue_ductility_exponent=mp["fatigue_ductility_exponent"],
        shear_modulus_GPa=mp["shear_modulus_GPa"],
    )
    cycles = [
        ThermalCycle(
            cycle_id=c["cycle_id"],
            T_min_C=c["T_min_C"],
            T_max_C=c["T_max_C"],
            ramp_rate_C_per_min=c["ramp_rate_C_per_min"],
            dwell_min_min=c["dwell_min_min"],
            plastic_strain_range=c["plastic_strain_range"],
        )
        for c in raw["thermal_cycles"]
    ]
    return SimulationReport(
        simulation_id=raw["simulation_id"],
        component=raw["component"],
        material=raw["material"],
        material_properties=mat,
        thermal_cycles=cycles,
        fea_solver=raw.get("fea_solver", "Unknown"),
        mesh_elements=raw.get("mesh_elements", 0),
        convergence_criterion=raw.get("convergence_criterion", 0.0),
        geometry=raw.get("geometry", {}),
    )


def load_csv_report(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation report not found: {path}")
    df = pd.read_csv(path)
    missing = REQUIRED_CSV_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in CSV: {sorted(missing)}")
    return df
