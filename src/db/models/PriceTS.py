from sqlalchemy import Integer, BigInteger, Date, Numeric, Index, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from datetime import date
from src.db.models import Base


class PriceTS(Base):
    __tablename__ = "price_ts"
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.product_id"),
        nullable=False)
    dt: Mapped[date] = mapped_column(Date, nullable=False)
    price_sale: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_pct: Mapped[float] = mapped_column(Numeric(5,2))

    product =  relationship("Product", back_populates="prices")

    __table_args__ = (
        Index("idx_prices_product_dt", "product_id", "dt"),
    )