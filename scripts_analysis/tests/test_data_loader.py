import json
import os
import tempfile
import pytest
import pandas as pd
from scripts_analysis.data_loader import (
    ThermalCycle,
    MaterialProperties,
    SimulationReport,
    load_json_report,
    load_csv_report,
)

SAMPLE_JSON = {
    "simulation_id": "TEST_001",
    "component": "Test Component",
    "material": "SAC305",
    "geometry": {"standoff_height_um": 100, "bump_diameter_um": 150, "dnp_max_mm": 15.2},
    "material_properties": {
        "elastic_modulus_GPa": 51.0,
        "poissons_ratio": 0.36,
        "CTE_ppm_per_C": 21.0,
        "substrate_CTE_ppm_per_C": 3.2,
        "fatigue_ductility_coefficient": 0.325,
        "fatigue_ductility_exponent": -0.527,
        "shear_modulus_GPa": 18.7,
    },
    "thermal_cycles": [
        {"cycle_id": 1, "T_min_C": -40, "T_max_C": 125,
         "ramp_rate_C_per_min": 10, "dwell_min_min": 10, "plastic_strain_range": 0.0082},
        {"cycle_id": 2, "T_min_C": -40, "T_max_C": 125,
         "ramp_rate_C_per_min": 10, "dwell_min_min": 10, "plastic_strain_range": 0.0085},
    ],
    "fea_solver": "Ansys Mechanical 2024 R1",
    "mesh_elements": 187432,
    "convergence_criterion": 1e-5,
}

SAMPLE_CSV = (
    "cycle_id,T_min_C,T_max_C,ramp_rate_C_per_min,dwell_min_min,"
    "plastic_strain_range,accumulated_damage\n"
    "1,-40,125,10,10,0.0082,0.0\n"
    "2,-40,125,10,10,0.0085,0.0\n"
)


def _tmp(suffix, content):
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w") as f:
        json.dump(content, f) if isinstance(content, dict) else f.write(content)
    return path


class TestLoadJsonReport:
    def test_returns_simulation_report(self):
        p = _tmp(".json", SAMPLE_JSON)
        assert isinstance(load_json_report(p), SimulationReport)
        os.unlink(p)

    def test_simulation_id_parsed(self):
        p = _tmp(".json", SAMPLE_JSON)
        assert load_json_report(p).simulation_id == "TEST_001"
        os.unlink(p)

    def test_material_properties_parsed(self):
        p = _tmp(".json", SAMPLE_JSON)
        mp = load_json_report(p).material_properties
        assert mp.fatigue_ductility_coefficient == pytest.approx(0.325)
        assert mp.fatigue_ductility_exponent == pytest.approx(-0.527)
        os.unlink(p)

    def test_thermal_cycles_count(self):
        p = _tmp(".json", SAMPLE_JSON)
        assert len(load_json_report(p).thermal_cycles) == 2
        os.unlink(p)

    def test_thermal_cycle_fields(self):
        p = _tmp(".json", SAMPLE_JSON)
        c = load_json_report(p).thermal_cycles[0]
        assert c.T_min_C == -40
        assert c.T_max_C == 125
        assert c.plastic_strain_range == pytest.approx(0.0082)
        os.unlink(p)

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_json_report("/nonexistent/path.json")

    def test_raises_on_invalid_json(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            f.write("not json {{{")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_json_report(path)
        os.unlink(path)


class TestLoadCsvReport:
    def test_returns_dataframe(self):
        p = _tmp(".csv", SAMPLE_CSV)
        assert isinstance(load_csv_report(p), pd.DataFrame)
        os.unlink(p)

    def test_required_columns_present(self):
        p = _tmp(".csv", SAMPLE_CSV)
        df = load_csv_report(p)
        for col in ("cycle_id", "T_min_C", "T_max_C", "plastic_strain_range"):
            assert col in df.columns
        os.unlink(p)

    def test_row_count(self):
        p = _tmp(".csv", SAMPLE_CSV)
        assert len(load_csv_report(p)) == 2
        os.unlink(p)

    def test_raises_on_missing_columns(self):
        p = _tmp(".csv", "cycle_id,T_min_C\n1,-40\n")
        with pytest.raises(ValueError, match="Missing columns"):
            load_csv_report(p)
        os.unlink(p)
