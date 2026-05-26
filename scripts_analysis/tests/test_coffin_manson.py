import pytest
from scripts_analysis.coffin_manson import (
    cycles_to_failure,
    engelmaier_exponent,
    miner_damage,
    lifetime_estimate,
    FailureRisk,
)
from scripts_analysis.data_loader import MaterialProperties, ThermalCycle

MAT = MaterialProperties(
    elastic_modulus_GPa=51.0,
    poissons_ratio=0.36,
    CTE_ppm_per_C=21.0,
    substrate_CTE_ppm_per_C=3.2,
    fatigue_ductility_coefficient=0.325,
    fatigue_ductility_exponent=-0.527,
    shear_modulus_GPa=18.7,
)
CYCLE_MILD   = ThermalCycle(1, -40, 125, 10, 10, 0.0082)
CYCLE_SEVERE = ThermalCycle(2, -65, 150, 20,  5, 0.0145)


class TestCyclesToFailure:
    def test_returns_positive_float(self):
        assert cycles_to_failure(CYCLE_MILD, MAT) > 0

    def test_higher_strain_fewer_cycles(self):
        assert cycles_to_failure(CYCLE_SEVERE, MAT) < cycles_to_failure(CYCLE_MILD, MAT)

    def test_known_value_sac305(self):
        expected = 0.5 * ((0.0082 / 0.325) ** (1.0 / -0.527))
        assert cycles_to_failure(CYCLE_MILD, MAT) == pytest.approx(expected, rel=1e-6)

    def test_raises_on_zero_strain(self):
        bad = ThermalCycle(99, -40, 125, 10, 10, 0.0)
        with pytest.raises(ValueError, match="plastic_strain_range must be positive"):
            cycles_to_failure(bad, MAT)


class TestEngelmaierExponent:
    def test_returns_negative_float(self):
        assert engelmaier_exponent(T_mean_C=42.5, freq_cycles_per_day=1.0) < 0

    def test_typical_range(self):
        c = engelmaier_exponent(T_mean_C=42.5, freq_cycles_per_day=1.0)
        assert -0.8 < c < -0.3

    def test_higher_temp_more_negative(self):
        c_low  = engelmaier_exponent(T_mean_C=20.0,  freq_cycles_per_day=1.0)
        c_high = engelmaier_exponent(T_mean_C=100.0, freq_cycles_per_day=1.0)
        assert c_high < c_low


class TestMinerDamage:
    def test_single_full_life(self):
        nf = cycles_to_failure(CYCLE_MILD, MAT)
        assert miner_damage([(CYCLE_MILD, nf)], MAT) == pytest.approx(1.0)

    def test_partial_damage(self):
        nf = cycles_to_failure(CYCLE_MILD, MAT)
        assert miner_damage([(CYCLE_MILD, nf / 2)], MAT) == pytest.approx(0.5, rel=1e-6)

    def test_mixed_damage_accumulates(self):
        nf_mild   = cycles_to_failure(CYCLE_MILD,   MAT)
        nf_severe = cycles_to_failure(CYCLE_SEVERE, MAT)
        d = miner_damage([(CYCLE_MILD, nf_mild / 4), (CYCLE_SEVERE, nf_severe / 4)], MAT)
        assert d == pytest.approx(0.5, rel=1e-6)


class TestLifetimeEstimate:
    def test_returns_expected_keys(self):
        result = lifetime_estimate([CYCLE_MILD] * 5, MAT)
        assert "cycles_to_failure_per_cycle_type" in result
        assert "miner_damage_per_cycle" in result
        assert "estimated_total_cycles" in result
        assert "risk" in result

    def test_risk_is_failure_risk(self):
        result = lifetime_estimate([CYCLE_MILD] * 3, MAT)
        assert isinstance(result["risk"], FailureRisk)

    def test_high_damage_gives_high_or_critical_risk(self):
        extreme = ThermalCycle(99, -65, 200, 30, 2, 0.05)
        result = lifetime_estimate([extreme] * 1000, MAT)
        assert result["risk"] in (FailureRisk.HIGH, FailureRisk.CRITICAL)
