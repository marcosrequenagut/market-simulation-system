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