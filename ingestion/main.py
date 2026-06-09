import time
import logging
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import Column, Date, Double, BigInteger, String, Numeric
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/market_data"
)

TICKERS = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^FTSE": "FTSE 100",
    "^DAX": "DAX",
    "^FCHI": "CAC 40",
    "^N225": "Nikkei 225",
    "^HSI": "Hang Seng",
    "GC=F": "Gold",
    "BTC-USD": "Bitcoin"
}

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def create_table_if_not_exists():
    """Create the market_prices table if it doesn't exist"""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS market_prices (
                date DATE NOT NULL,
                ticker VARCHAR(10) NOT NULL,
                open NUMERIC NOT NULL,
                high NUMERIC NOT NULL,
                low NUMERIC NOT NULL,
                close NUMERIC NOT NULL,
                volume BIGINT NOT NULL,
                PRIMARY KEY (date, ticker)
            )
        """))
        conn.commit()


def get_last_date(ticker: str) -> date | None:
    """Get the last date for a ticker from the database"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT MAX(date) FROM market_prices WHERE ticker = :ticker"),
            {"ticker": ticker}
        ).fetchone()
        return result[0] if result else None


def ingest_ticker(ticker: str) -> None:
    """Download and insert data for a single ticker"""
    try:
        last_date = get_last_date(ticker)

        if last_date is None:
            logger.info(f"{ticker}: No data found, downloading full history...")
            df = yf.Ticker(ticker).history(period="max")
        else:
            start = last_date + timedelta(days=1)
            if start >= date.today():
                logger.info(f"{ticker}: Already up to date")
                return
            logger.info(f"{ticker}: Downloading data from {start}")
            df = yf.Ticker(ticker).history(start=start.isoformat())

        if df.empty:
            logger.warning(f"{ticker}: No data retrievec")
            return
        
        df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"], utc=True).dt.date
        df["ticker"] = ticker

        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume"
        })

        df = df[["date", "ticker", "open", "high", "low", "close", "volume"]]
        
        df.to_sql(
            "market_prices",
            engine,
            if_exists="append",
            index=False
        )

        logger.info(f"{ticker}: Inserted {len(df)} rows")

    except Exception as e:
        logger.error(f"{ticker}: Error during ingestion - {e}")
        raise


def ingest_all() -> None:
    """Download and insert data for all tickers"""
    logger.info("Starting ingestion for all tickers")
    for ticker in TICKERS:
        ingest_ticker(ticker)
    logger.info("Ingestion completed")


if __name__ == "__main__":
    # Wait for Postgres to be ready
    time.sleep(15)
    create_table_if_not_exists()

    # Initial ingestion
    ingest_all()

    # Schedule daily update at 23:00
    scheduler = BlockingScheduler()
    scheduler.add_job(ingest_all, "cron", hour=23, minute=0)
    logger.info("Scheduler started, next update at 23:00")
    scheduler.start()
