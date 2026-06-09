FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    yfinance \
    pandas \
    sqlalchemy \
    psycopg2-binary \
    apscheduler

COPY ingestion/main.py .

CMD ["python", "main.py"]