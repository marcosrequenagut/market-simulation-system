import pytest
import random
from app.engine.montecarlo import run_monter_carlo, run_monter_carlo_lognormal


def test_monter_carlo_basic():
    """Basic Monte Carlo simulation"""
    random.seed(42)
    result = run_monter_carlo(1000, 0.10, 0.15, 10, 100)

    assert "p10" in result
    assert "p50" in result
    assert "p90" in result
    assert "min" in result
    assert "max" in result
    assert "simulations" in result
    assert result["simulations"] == 100
    assert result["min"] <= result["p10"] <= result["p50"] <= result["p90"] <= result["max"]


def test_monter_carlo_zero_volatility():
    """Zero volatility should produce consistent results"""
    random.seed(42)
    result = run_monter_carlo(1000, 0.10, 0, 5, 10)

    # With zero volatility, all results should be the same (within rounding)
    expected = 1000 * (1.10 ** 5)
    assert abs(result["p10"] - expected) < 0.01
    assert abs(result["p50"] - expected) < 0.01
    assert abs(result["p90"] - expected) < 0.01
    assert abs(result["min"] - expected) < 0.01
    assert abs(result["max"] - expected) < 0.01


def test_monter_carlo_negative_return():
    """Negative expected return"""
    random.seed(42)
    result = run_monter_carlo(1000, -0.05, 0.10, 5, 100)

    assert result["p50"] < 1000  # Should decrease on average
    assert result["simulations"] == 100


def test_monter_carlo_single_year():
    """Single year simulation"""
    random.seed(42)
    result = run_monter_carlo(1000, 0.10, 0.15, 1, 50)

    assert result["simulations"] == 50
    assert result["min"] > 0


def test_monter_carlo_high_volatility():
    """High volatility scenario"""
    random.seed(42)
    result = run_monter_carlo(1000, 0.10, 0.50, 10, 100)

    # High volatility should create wide spread
    assert result["max"] > result["min"] * 2


def test_monter_carlo_low_simulations():
    """Minimum number of simulations"""
    random.seed(42)
    result = run_monter_carlo(1000, 0.10, 0.15, 5, 1)

    assert result["simulations"] == 1
    assert result["min"] == result["max"]  # Only one simulation


def test_monter_carlo_zero_initial_investment():
    """Zero initial investment must raise ValueError"""
    with pytest.raises(ValueError, match="Initial investment must be greater than 0"):
        run_monter_carlo(0, 0.10, 0.15, 10, 100)


def test_monter_carlo_negative_initial_investment():
    """Negative initial investment must raise ValueError"""
    with pytest.raises(ValueError, match="Initial investment must be greater than 0"):
        run_monter_carlo(-1000, 0.10, 0.15, 10, 100)


def test_monter_carlo_zero_years():
    """Zero years must raise ValueError"""
    with pytest.raises(ValueError, match="Number of years must be greater than 0"):
        run_monter_carlo(1000, 0.10, 0.15, 0, 100)


def test_monter_carlo_negative_years():
    """Negative years must raise ValueError"""
    with pytest.raises(ValueError, match="Number of years must be greater than 0"):
        run_monter_carlo(1000, 0.10, 0.15, -5, 100)


def test_monter_carlo_zero_simulations():
    """Zero simulations must raise ValueError"""
    with pytest.raises(ValueError, match="Number of simulations must be greater than 0"):
        run_monter_carlo(1000, 0.10, 0.15, 10, 0)


def test_monter_carlo_negative_simulations():
    """Negative simulations must raise ValueError"""
    with pytest.raises(ValueError, match="Number of simulations must be greater than 0"):
        run_monter_carlo(1000, 0.10, 0.15, 10, -100)


def test_monter_carlo_negative_volatility():
    """Negative volatility must raise ValueError"""
    with pytest.raises(ValueError, match="Volatility cannot be negative"):
        run_monter_carlo(1000, 0.10, -0.15, 10, 100)


def test_monter_carlo_default_simulations():
    """Test default simulations parameter"""
    random.seed(42)
    result = run_monter_carlo(1000, 0.10, 0.15, 5)

    assert result["simulations"] == 1000


def test_monter_carlo_large_initial():
    """Large initial investment"""
    random.seed(42)
    result = run_monter_carlo(1000000, 0.07, 0.12, 20, 50)

    assert result["p50"] > 1000000
    assert result["simulations"] == 50


def test_monter_carlo_percentile_ordering():
    """Verify percentiles are correctly ordered"""
    random.seed(42)
    result = run_monter_carlo(1000, 0.10, 0.15, 10, 100)

    assert result["min"] <= result["p10"]
    assert result["p10"] <= result["p50"]
    assert result["p50"] <= result["p90"]
    assert result["p90"] <= result["max"]


def test_monter_carlo_lognormal_basic():
    """Basic lognormal Monte Carlo simulation"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, 0.10, 0.15, 10, 100)

    assert "p10" in result
    assert "p50" in result
    assert "p90" in result
    assert "min" in result
    assert "max" in result
    assert "simulations" in result
    assert result["simulations"] == 100
    assert result["min"] > 0  # Lognormal prevents negative values
    assert result["min"] <= result["p10"] <= result["p50"] <= result["p90"] <= result["max"]


def test_monter_carlo_lognormal_zero_volatility():
    """Zero volatility with lognormal distribution"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, 0.10, 0, 5, 10)

    # With zero volatility, mu = log(1.1) and results should be deterministic
    expected = 1000 * ((1.10) ** 5)
    assert abs(result["p10"] - expected) < 1.0
    assert abs(result["p50"] - expected) < 1.0
    assert abs(result["p90"] - expected) < 1.0


def test_monter_carlo_lognormal_negative_return():
    """Negative expected return with lognormal"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, -0.05, 0.10, 5, 100)

    assert result["p50"] < 1000  # Should decrease on average
    assert result["min"] > 0  # Still positive due to lognormal
    assert result["simulations"] == 100


def test_monter_carlo_lognormal_single_year():
    """Single year simulation with lognormal"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, 0.10, 0.15, 1, 50)

    assert result["simulations"] == 50
    assert result["min"] > 0


def test_monter_carlo_lognormal_high_volatility():
    """High volatility scenario with lognormal"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, 0.10, 0.50, 10, 100)

    # High volatility should create wide spread
    assert result["max"] > result["min"] * 2
    assert result["min"] > 0  # No negative values


def test_monter_carlo_lognormal_low_simulations():
    """Minimum number of simulations with lognormal"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, 0.10, 0.15, 5, 1)
    
    assert result["simulations"] == 1
    assert result["min"] == result["max"]  # Only one simulation


def test_monter_carlo_lognormal_zero_initial_investment():
    """Zero initial investment must raise ValueError"""
    with pytest.raises(ValueError, match="Initial investment must be greater than 0"):
        run_monter_carlo_lognormal(0, 0.10, 0.15, 10, 100)


def test_monter_carlo_lognormal_negative_initial_investment():
    """Negative initial investment must raise ValueError"""
    with pytest.raises(ValueError, match="Initial investment must be greater than 0"):
        run_monter_carlo_lognormal(-1000, 0.10, 0.15, 10, 100)


def test_monter_carlo_lognormal_zero_years():
    """Zero years must raise ValueError"""
    with pytest.raises(ValueError, match="Number of years must be greater than 0"):
        run_monter_carlo_lognormal(1000, 0.10, 0.15, 0, 100)


def test_monter_carlo_lognormal_negative_years():
    """Negative years must raise ValueError"""
    with pytest.raises(ValueError, match="Number of years must be greater than 0"):
        run_monter_carlo_lognormal(1000, 0.10, 0.15, -5, 100)


def test_monter_carlo_lognormal_zero_simulations():
    """Zero simulations must raise ValueError"""
    with pytest.raises(ValueError, match="Number of simulations must be greater than 0"):
        run_monter_carlo_lognormal(1000, 0.10, 0.15, 10, 0)


def test_monter_carlo_lognormal_negative_simulations():
    """Negative simulations must raise ValueError"""
    with pytest.raises(ValueError, match="Number of simulations must be greater than 0"):
        run_monter_carlo_lognormal(1000, 0.10, 0.15, 10, -100)


def test_monter_carlo_lognormal_negative_volatility():
    """Negative volatility must raise ValueError"""
    with pytest.raises(ValueError, match="Volatility cannot be negative"):
        run_monter_carlo_lognormal(1000, 0.10, -0.15, 10, 100)


def test_monter_carlo_lognormal_default_simulations():
    """Test default simulations parameter"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, 0.10, 0.15, 5)

    assert result["simulations"] == 1000


def test_monter_carlo_lognormal_large_initial():
    """Large initial investment with lognormal"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000000, 0.07, 0.12, 20, 50)

    assert result["p50"] > 1000000
    assert result["simulations"] == 50


def test_monter_carlo_lognormal_percentile_ordering():
    """Verify percentiles are correctly ordered with lognormal"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, 0.10, 0.15, 10, 100)

    assert result["min"] <= result["p10"]
    assert result["p10"] <= result["p50"]
    assert result["p50"] <= result["p90"]
    assert result["p90"] <= result["max"]


def test_monter_carlo_lognormal_no_negative_values():
    """Key feature: lognormal distribution prevents negative portfolio values"""
    random.seed(42)
    result = run_monter_carlo_lognormal(1000, -0.50, 0.30, 10, 1000)

    # Even with very negative expected return and high volatility,
    # all values should remain positive
    assert result["min"] > 0
