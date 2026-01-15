from sqlalchemy import (
    Column, Integer, BigInteger, Text, Boolean,
    Numeric, Date, DateTime, ForeignKey, Index, func
)
from sqlalchemy.orm import relationship







class UserFavorite(Base):
    __tablename__ = "user_favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    added_at = Column(Date, nullable=False, server_default=func.current_date())
