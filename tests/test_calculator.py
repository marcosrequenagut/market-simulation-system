import pytest
from app.engine.calculator import calculate_cagr

def test_cagr_basic():
    """1000 -> 2500 over 10 years = ~9.6%"""
    result = calculate_cagr(1000, 2500, 10)
    assert abs(result - 0.096) < 0.001

def test_cagr_exact():
    """Exact case: double in 1 year = 100%"""
    result = calculate_cagr(1000, 2000, 1)
    assert result == 1.0

def test_cagr_no_growth():
    """No growth = 0%"""
    result = calculate_cagr(1000, 1000, 5)
    assert result == 0.0

def test_cagr_initial_value_zero():
    """Initial value 0 must raise ValueError"""
    with pytest.raises(ValueError):
        calculate_cagr(0, 2500, 10)

def test_cagr_negative_years():
    """Negative years must raise ValueError"""
    with pytest.raises(ValueError):
        calculate_cagr(1000, 2500, -5)

def test_cagr_negative_final_value():
    """Negative final value must raise ValueError"""
    with pytest.raises(ValueError):
        calculate_cagr(1000, -2500, 10)
