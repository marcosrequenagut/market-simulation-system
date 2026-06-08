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