from sqlalchemy import Integer, BigInteger, Date, Numeric, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from datetime import date
from src.db.models import Base


class SalesProxyTS(Base):
    __tablename__ = "sales_proxy_ts"
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.product_id"),
        nullable=False)
    dt: Mapped[date] = mapped_column(Date, nullable=False)
    sales: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(default=0.85)

    product = relationship("Product", back_populates="sales_proxies")

    __table_args__ = (
        UniqueConstraint("product_id", "dt", name="uq_sales_product_dt"),
    )