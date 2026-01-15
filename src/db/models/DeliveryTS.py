from sqlalchemy import Integer, BigInteger, Date, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column

from datetime import date
from src.db.models import Base

class DeliveryTS(Base):
    __tablename__ = "delivery_ts"
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.product_id"),
        nullable=False)
    dt: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_days: Mapped[int] = mapped_column(Integer)

    product = relationship("Product", back_populates="deliveries")