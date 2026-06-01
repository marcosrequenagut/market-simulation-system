# Create the CAGR (Compound Annual Growth Rate) calculator

def calculate_cagr(initial_value: float, final_value: float, years: int) -> float:
    """
    Calculate the Compound Annual Growth Rate.

    Args:
        initial_value: initial value of the investment
        final_value: final value of the investment
        years: number of years

    Returns:
        CAGR as decimal (0.096 = 9.6%)

    Raises:
        ValueError: If values are invalid
    """

    if initial_value <= 0:
        raise ValueError("Initial value must be positive and greater than zero")

    if final_value <= 0:
        raise ValueError("Final value must be positive and greater than zero")

    if years <= 0:
        raise ValueError("Years must be positive and greater than zero")

    return (final_value / initial_value) ** (1 / years) - 1


def calculate_compound_interest(
    initial_investment: float,
    monthly_contribution: float,
    annual_rate: float,
    years: int
) -> dict:
    """
    Calculate compound interest with monthly contributions.

    Args:
        initial_investment: Initial amount invested
        monthly_contribution: Amount added every month
        annual_rate: Annual interest rate as decimal (0.07 = 7%)
        years: Number of years

    Returns:
        Dictionary with final_value, total_invested and total_interest

    Raises:
        ValueError: If any value is invalid
    """

    if initial_investment < 0:
        raise ValueError("Initial investment cannot be negative")
    if monthly_contribution < 0:
        raise ValueError("Monthly contribution cannot be negative")
    if annual_rate < 0:
        raise ValueError("Annual rate cannot be negative")
    if years <= 0:
        raise ValueError("Number of years must be greater than 0")

    monthly_rate = annual_rate / 12
    months = years * 12
    balance = initial_investment

    for _ in range(months):
        balance = balance * (1 + monthly_rate) + monthly_contribution

    total_invested = initial_investment + (monthly_contribution * months)
    total_interest = balance - total_invested

    return {
        "final_value": round(balance, 2),
        "total_invested": round(total_invested, 2),
        "total_interest": round(total_interest, 2)
    }
