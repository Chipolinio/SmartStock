from sqlalchemy import Integer, BigInteger, Date, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from datetime import date
from src.db.models import Base

class StockTS(Base):
    __tablename__ = "stock_ts"
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.product_id"),
        nullable=False)
    dt: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    product = relationship(lambda: Product, back_populates="stocks")

    __table_args__ = (
        UniqueConstraint("product_id", "dt", name="uq_stock_product_dt"),
    )


from src.db.models.Product import Product