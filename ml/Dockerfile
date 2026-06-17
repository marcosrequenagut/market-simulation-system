FROM python:3.11-slim

WORKDIR /app

ENV GIT_PYTHON_REFRESH=quiet

RUN pip install --no-cache-dir \
    sqlalchemy \
    psycopg2-binary \
    pandas \
    "mlflow==2.13.0" \
    statsmodels \
    scikit-learn \
    xgboost \
    numpy

COPY ml/ ./ml/

CMD ["python", "-m", "ml.train_arima"]