from sqlalchemy import Column, Date, Double, BigInteger, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class MarketPrice(Base):
    """SQLAlchemy model for market_prices table."""

    __tablename__ = "market_prices"

    date = Column(Date, primary_key=True)
    ticker = Column(String(20), primary_key=True)
    open = Column(Double)
    high = Column(Double)
    low = Column(Double)
    close = Column(Double)
    volume = Column(BigInteger)

    def to_dict(self):
        return {
            "date": self.date.isoformat(),
            "ticker": self.ticker,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }
