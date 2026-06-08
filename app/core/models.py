from sqlalchemy import Column, Date, Double, BigInteger
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class SP500Price(Base):
    """SQLAlchemy model for sp500_prices table."""

    __tablename__ = "sp500_prices"

    date = Column(Date, primary_key=True)
    open = Column(Double)
    high = Column(Double)
    low = Column(Double)
    close = Column(Double)
    volume = Column(BigInteger)

    def to_dict(self):
        return {
            "date": self.date.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }
