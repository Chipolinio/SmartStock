from pydantic import BaseModel
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped
from sqlalchemy.testing.schema import mapped_column


class User(BaseModel):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    is_pro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)