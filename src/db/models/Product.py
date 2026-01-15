from sqlalchemy import String, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.db.models.Base import Base


class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String)
    entity: Mapped[str] = mapped_column(String)

    prices = relationship("PriceTS", back_populates="product", cascade="all, delete-orphan")
    stocks = relationship("StockTS", back_populates="product", cascade="all, delete-orphan")
    socials = relationship("SocialTS", back_populates="product", cascade="all, delete-orphan")
    deliveries = relationship("DeliveryTS", back_populates="product", cascade="all, delete-orphan")
    sales_proxies = relationship("SalesProxyTS", back_populates="product", cascade="all, delete-orphan")
    features = relationship("ProductFeaturesDaily", back_populates="product", cascade="all, delete-orphan")
    predictions = relationship("PredictedSalesTS", back_populates="product", cascade="all, delete-orphan")
    favorited_by: Mapped[list["UserFavorite"]] = relationship(back_populates="product", cascade="all, delete-orphan")