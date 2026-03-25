from sqlalchemy import Integer, BigInteger, Date, Numeric, ForeignKey, UniqueConstraint
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

    product = relationship(lambda: Product, back_populates="socials")

    __table_args__ = (
        UniqueConstraint("product_id", "dt", name="uq_social_product_dt"),
    )


from src.db.models.Product import Product