from sqlalchemy import String, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.Base import Base


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    is_pro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    favorites: Mapped[list["UserFavorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")