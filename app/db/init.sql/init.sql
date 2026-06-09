CREATE TABLE IF NOT EXISTS market_prices(
    date DATE NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    volume BIGINT,
    PRIMARY KEY (date, ticker)
);
