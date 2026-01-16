from sqlalchemy import Integer, BigInteger, Date, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, relationship, mapped_column

from datetime import date
from src.db.models import Base

class SocialTS(Base):
    __tablename__ = "social_ts"
    product_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("products.product_id"),
        nullable=False)
    dt: Mapped[date] = mapped_column(Date, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3,2))
    feedbacks: Mapped[int] = mapped_column(Integer)

    product = relationship("Product", back_populates="socials")

    __table_args__ = (
        Index("idx_features_product_dt", "product_id", "dt"),
    )