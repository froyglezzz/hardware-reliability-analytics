import os
import tempfile
import pytest
import matplotlib
matplotlib.use("Agg")

from scripts_analysis.data_loader import MaterialProperties, ThermalCycle
from scripts_analysis.visualization import (
    plot_degradation_curve,
    plot_woehler_diagram,
    plot_damage_accumulation,
)

MAT = MaterialProperties(51.0, 0.36, 21.0, 3.2, 0.325, -0.527, 18.7)
CYCLES = [ThermalCycle(i, -40, 125, 10, 10, 0.0080 + i * 0.0002) for i in range(1, 11)]


class TestPlotDegradationCurve:
    def test_saves_png(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "deg.png")
            plot_degradation_curve(CYCLES, MAT, output_path=out)
            assert os.path.exists(out) and os.path.getsize(out) > 0

    def test_returns_output_path(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "deg.png")
            assert plot_degradation_curve(CYCLES, MAT, output_path=out) == out


class TestPlotWoehlerDiagram:
    def test_saves_png(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "sn.png")
            plot_woehler_diagram([0.002, 0.005, 0.008, 0.015, 0.030], MAT, output_path=out)
            assert os.path.exists(out)

    def test_raises_on_empty(self):
        with pytest.raises(ValueError, match="strain_range_values must not be empty"):
            plot_woehler_diagram([], MAT, output_path="/tmp/x.png")


class TestPlotDamageAccumulation:
    def test_saves_png(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "dmg.png")
            plot_damage_accumulation([0.01 * i for i in range(1, 21)], output_path=out)
            assert os.path.exists(out)

    def test_raises_on_empty(self):
        with pytest.raises(ValueError, match="damage_sequence must not be empty"):
            plot_damage_accumulation([], output_path="/tmp/x.png")
