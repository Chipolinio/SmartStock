from sqlalchemy import BigInteger, Date, ForeignKey, func
from sqlalchemy.orm import Mapped, relationship, mapped_column

from datetime import date
from src.db.models import Base


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    added_at: Mapped[date] = mapped_column(Date, nullable=False, server_default=func.current_date())

    user: Mapped["User"] = relationship(back_populates="favorites")
    product: Mapped["Product"] = relationship(back_populates="favorited_by")