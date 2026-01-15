from sqlalchemy import Integer, BigInteger, Date, Numeric, Index, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from datetime import date
from src.db.models import Base


class ProductFeaturesDaily(Base):
    __tablename__ = "product_features_daily"
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.product_id"),
        nullable=False)
    dt: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount_pct: Mapped[float] = mapped_column(Numeric(5, 2))
    rating: Mapped[float] = mapped_column(Numeric(3, 2))
    feedbacks: Mapped[int] = mapped_column(Integer)
    avg_sales_7d: Mapped[float] = mapped_column(Numeric(12, 2))
    avg_sales_14d: Mapped[float] = mapped_column(Numeric(12, 2))
    stock_left: Mapped[int] = mapped_column(Integer, nullable=False)
    days_to_oos: Mapped[float] = mapped_column(Numeric(10, 2))
    price_rank_in_category: Mapped[int] = mapped_column(Integer)
    rating_rank_in_category: Mapped[int] = mapped_column(Integer)

    product = relationship("Product", back_populates="features")

    __table_args__ = (Index("idx_features_dt", "dt"),)