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
