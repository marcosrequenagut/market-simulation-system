import random
import math


def run_monte_carlo(
    initial_investment: float,
    annual_return: float,
    annual_volatility: float,
    years: int,
    simulations: int = 1000
):
    """
    Run a Monte Carlo simulation for portfolio evolution.

    Args:
        initial_investment: Initial amount invested
        annual_return: Expected annual return as decimal (0.10 = 10%)
        annual_volatility: Annual volatility as decimal (0.15 = 15%)
        years: Number of years to simulate
        simulations: Number of simulation runs (default 1000)

    Returns:
        Dictionary with percentile results: p10, p50, p90 and all results

    Raises:
        ValueError: If any value is invalid
    """

    if initial_investment <= 0:
        raise ValueError("Initial investment must be greater than 0")
    if years <= 0:
        raise ValueError("Number of years must be greater than 0")
    if simulations <= 0:
        raise ValueError("Number of simulations must be greater than 0")
    if annual_volatility < 0:
        raise ValueError("Volatility cannot be negative")

    results = []

    for _ in range(simulations):
        balance = initial_investment
        for _ in range(years):
            yearly_return = random.gauss(annual_return, annual_volatility)
            balance *= (1 + yearly_return)
        results.append(balance)

    results.sort()
    p10 = results[int(0.1 * len(results))]
    p50 = results[int(0.5 * len(results))]
    p90 = results[int(0.9 * len(results))]

    return {
        "p10": p10,
        "p50": p50,
        "p90": p90,
        "min": results[0],
        "max": results[-1],
        "simulations": simulations
    }


def run_monte_carlo_lognormal(
    initial_investment: float,
    annual_return: float,
    annual_volatility: float,
    years: int,
    simulations: int = 1000,
    monthly_contribution: float = 0.0
):
    if initial_investment <= 0:
        raise ValueError("Initial investment must be greater than 0")
    if years <= 0:
        raise ValueError("Number of years must be greater than 0")
    if simulations <= 0:
        raise ValueError("Number of simulations must be greater than 0")
    if annual_volatility < 0:
        raise ValueError("Volatility cannot be negative")

    results = []
    mu = math.log(1 + annual_return) - 0.5 * annual_volatility ** 2
    sigma = annual_volatility
    monthly_rate = mu / 12
    monthly_sigma = sigma / (12 ** 0.5)

    for _ in range(simulations):
        balance = initial_investment
        for _ in range(years * 12):
            monthly_return = random.gauss(monthly_rate, monthly_sigma)
            balance = balance * math.exp(monthly_return) + monthly_contribution
        results.append(round(balance, 2))

    results.sort()
    p10 = results[int(simulations * 0.10)]
    p50 = results[int(simulations * 0.50)]
    p90 = results[int(simulations * 0.90)]

    return {
        "p10": p10,
        "p50": p50,
        "p90": p90,
        "min": results[0],
        "max": results[-1],
        "simulations": simulations
    }
