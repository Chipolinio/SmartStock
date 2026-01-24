from sqlalchemy import BigInteger, Date, Numeric, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship, mapped_column

from datetime import date
from src.db.models import Base


class PredictedSalesTS(Base):
    __tablename__ = "predicted_sales_ts"
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.product_id"),
        nullable=False)
    dt: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_sales: Mapped[float]  = mapped_column(Numeric(12, 2), nullable=False)
    model_version: Mapped[str]  = mapped_column(String, nullable=False)

    product = relationship("Product", back_populates="predictions")

    __table_args__ = (
        UniqueConstraint( "product_id", "dt", name="uq_predicted_sales_product_dt"),
    )