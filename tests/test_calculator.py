import pytest
from app.engine.calculator import calculate_cagr, calculate_compound_interest


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


def test_compound_interest_basic():
    """Basic case with initial investment and monthly contributions"""
    result = calculate_compound_interest(1000, 100, 0.07, 5)
    assert result["final_value"] > 0
    assert result["total_invested"] == 7000  # 1000 + (100 * 60)
    assert result["total_interest"] > 0
    assert result["final_value"] == result["total_invested"] + result["total_interest"]


def test_compound_interest_zero_initial():
    """Zero initial investment with monthly contributions"""
    result = calculate_compound_interest(0, 100, 0.07, 5)
    assert result["final_value"] > 0
    assert result["total_invested"] == 6000  # 0 + (100 * 60)
    assert result["total_interest"] > 0


def test_compound_interest_zero_monthly():
    """Zero monthly contribution, only initial investment"""
    result = calculate_compound_interest(1000, 0, 0.07, 5)
    assert result["final_value"] > 1000
    assert result["total_invested"] == 1000
    assert result["total_interest"] > 0


def test_compound_interest_zero_rate():
    """Zero interest rate, no growth"""
    result = calculate_compound_interest(1000, 100, 0, 5)
    assert result["final_value"] == 7000  # 1000 + (100 * 60)
    assert result["total_invested"] == 7000
    assert result["total_interest"] == 0


def test_compound_interest_negative_initial():
    """Negative initial investment must raise ValueError"""
    with pytest.raises(ValueError, match="Initial investment cannot be negative"):
        calculate_compound_interest(-1000, 100, 0.07, 5)


def test_compound_interest_negative_monthly():
    """Negative monthly contribution must raise ValueError"""
    with pytest.raises(ValueError, match="Monthly contribution cannot be negative"):
        calculate_compound_interest(1000, -100, 0.07, 5)


def test_compound_interest_negative_rate():
    """Negative annual rate must raise ValueError"""
    with pytest.raises(ValueError, match="Annual rate cannot be negative"):
        calculate_compound_interest(1000, 100, -0.07, 5)


def test_compound_interest_zero_years():
    """Zero years must raise ValueError"""
    with pytest.raises(ValueError, match="Number of years must be greater than 0"):
        calculate_compound_interest(1000, 100, 0.07, 0)


def test_compound_interest_negative_years():
    """Negative years must raise ValueError"""
    with pytest.raises(ValueError, match="Number of years must be greater than 0"):
        calculate_compound_interest(1000, 100, 0.07, -5)


def test_compound_interest_one_year():
    """Single year calculation"""
    result = calculate_compound_interest(1000, 100, 0.12, 1)
    assert result["total_invested"] == 2200  # 1000 + (100 * 12)
    assert result["final_value"] > 2200
    assert result["total_interest"] > 0


def test_compound_interest_high_rate():
    """High interest rate scenario"""
    result = calculate_compound_interest(1000, 100, 0.20, 10)
    assert result["final_value"] > result["total_invested"]
    assert result["total_interest"] > 0
