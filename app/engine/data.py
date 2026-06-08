import yfinance as yf


def get_sp500_data(period: str = "10y") -> dict:
    """
    Fetch historical metrics for S&P 500 using yfinance.

    Args:
        period: Time period to fetch (1y, 5y, 10y, max)

    Returns:
        Dictionary with historical prices, annual return and volatility

    Raises:
        ValueError: If period is invalid
    """
    valid_periods = []
    max_years = 100

    for i in range(1, max_years + 1):
        valid_periods.append(f"{i}y")

    if period not in valid_periods:
        raise ValueError(f"Invalid period. Must be one of: {valid_periods}")

    # Fetch data
    ticker = yf.Ticker("^GSPC")
    hist = ticker.history(period=period)  # df with daily data

    if hist.empty:
        raise ValueError("No data available for the specified period")

    daily_returns = hist["Close"].pct_change().dropna()  # daily returns, it takes the current price and divides it by the previous price

    # We multiply by 252 because the market is open ~252 days a year
    annual_return = float(daily_returns.mean() * 252)
    annual_volatility = float(daily_returns.std() * (252 ** 0.5))

    return {
        "period": period,
        "annual_return": round(annual_return, 4),
        "annual_volatility": round(annual_volatility, 4),
        "start_price": round(float(hist["Close"].iloc[0]), 2),  # initial price of the period
        "end_price": round(float(hist["Close"].iloc[-1]), 2),  # final price of the period
        "data_points": len(hist)
    }
