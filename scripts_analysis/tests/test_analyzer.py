import json
import os
import tempfile
import pytest
from scripts_analysis.analyzer import run_analysis, AnalysisResult

REPORT = {
    "simulation_id": "INTEGRATION_001",
    "component": "Test MCM",
    "material": "SAC305",
    "geometry": {"standoff_height_um": 100, "bump_diameter_um": 150, "dnp_max_mm": 10.0},
    "material_properties": {
        "elastic_modulus_GPa": 51.0, "poissons_ratio": 0.36,
        "CTE_ppm_per_C": 21.0, "substrate_CTE_ppm_per_C": 3.2,
        "fatigue_ductility_coefficient": 0.325, "fatigue_ductility_exponent": -0.527,
        "shear_modulus_GPa": 18.7,
    },
    "thermal_cycles": [
        {"cycle_id": 1, "T_min_C": -40, "T_max_C": 125,
         "ramp_rate_C_per_min": 10, "dwell_min_min": 10, "plastic_strain_range": 0.0082},
        {"cycle_id": 2, "T_min_C": -40, "T_max_C": 125,
         "ramp_rate_C_per_min": 10, "dwell_min_min": 10, "plastic_strain_range": 0.0085},
    ],
    "fea_solver": "Ansys Mechanical 2024 R1",
    "mesh_elements": 50000,
    "convergence_criterion": 1e-5,
}


class TestRunAnalysis:
    def test_returns_analysis_result(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "report.json")
            with open(p, "w") as f:
                json.dump(REPORT, f)
            assert isinstance(run_analysis(p, output_dir=d), AnalysisResult)

    def test_plots_created(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "report.json")
            with open(p, "w") as f:
                json.dump(REPORT, f)
            result = run_analysis(p, output_dir=d)
            for path in result.plot_paths:
                assert os.path.exists(path), f"Missing: {path}"

    def test_result_has_lifetime_info(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "report.json")
            with open(p, "w") as f:
                json.dump(REPORT, f)
            result = run_analysis(p, output_dir=d)
            assert result.estimated_total_cycles > 0
            assert result.risk is not None
