# market-simulation-system
A financial portfolio simulation and analytics platform for modeling investment strategies, analyzing returns, and evaluating risk using historical market data and simulations like Monte Carlo one. Includes automated testing, CI/CD pipelines, and code quality analysis.

# To run the api without using docker
```bash
python -m uvicorn app.main:app --reload
```

# To run whne de app. method is not detected
```bash
python -m data_pipeline.load_initial_data_into_postgres_db
```

# Si de un dia para otro se ejecuta la API hay que asegurarse de que los datos de la base de datos están actualizados hasta el ultimo dia por eso jhay que ejecutar este scirpt: si al menos llevamos 1 o mas dias sin ejecutarlo:

docker exec -it sp500_backend python app/data_pipeline/get_all_historical_data.py

The XGBoost model predicts only the next day's return (the percentage change), not the price itself. In the future forecast, the first prediction starts from a real market price, but from that point onward, each predicted price is calculated using the previous predicted price rather than a real one.

This means that if the model makes a 0.1% error on day one, day two starts from an already incorrect price, day three starts from an even more inaccurate one, and so on. The forecasting error accumulates recursively, and the longer the prediction horizon, the further the forecast may drift from reality.

To illustrate this effect, the backtest includes two versions. The first anchors each prediction to the actual price from the previous day. In this setup, the model only needs to predict a single-day return and never accumulates forecasting errors, which is why the predicted line often overlaps closely with the real price series.

The second version replicates exactly how the future forecast works in practice. It starts from the first real price in the test set and recursively applies each prediction to the previous predicted value, allowing errors to accumulate just as they would in production. This second chart provides a much more realistic assessment of the model's performance and helps visually evaluate how reliable the future forecast is likely to be.

SARIMA is a linear model that, when applied to time series with very low autocorrelation (such as daily S&P 500 returns, which are close to white noise), tends to quickly converge to the series’ historical mean. The predicted returns are extremely small (around 0.0001–0.003), essentially zero, and after about day 5–6 they become almost constant, with only negligible fluctuations.

This is consistent with theory: if daily returns have little predictable structure, the best long-term forecast is simply the mean (approximately 0% for the S&P 500). This explains why SARIMA produces an almost flat forecast, while XGBoost, using additional features such as RSI, momentum, and volatility, generates more variable predictions, although these also tend to accumulate error over time.

Overall, this is an interesting result for analysis: the statistical model quickly “gives up” and reverts to the mean, while the more complex XGBoost attempts to capture patterns, but without necessarily improving true predictive accuracy.