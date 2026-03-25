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

    prices = relationship(lambda: PriceTS, back_populates="product", cascade="all, delete-orphan")
    stocks = relationship(lambda: StockTS, back_populates="product", cascade="all, delete-orphan")
    socials = relationship(lambda: SocialTS, back_populates="product", cascade="all, delete-orphan")
    deliveries = relationship(lambda: DeliveryTS, back_populates="product", cascade="all, delete-orphan")
    sales_proxies = relationship(lambda: SalesProxyTS, back_populates="product", cascade="all, delete-orphan")
    features = relationship(lambda: ProductFeaturesDaily, back_populates="product", cascade="all, delete-orphan")
    predictions = relationship(lambda: PredictedSalesTS, back_populates="product", cascade="all, delete-orphan")
    favorited_by: Mapped[list["UserFavorite"]] = relationship(back_populates="product", cascade="all, delete-orphan")


# Импортируем после определения класса для корректной работы lambda-relationships
from src.db.models.PriceTS import PriceTS
from src.db.models.StockTS import StockTS
from src.db.models.SocialTS import SocialTS
from src.db.models.DeliveryTS import DeliveryTS
from src.db.models.SalesProxyTS import SalesProxyTS
from src.db.models.ProductFeaturesDaily import ProductFeaturesDaily
from src.db.models.PredictedSalesTS import PredictedSalesTS
from src.db.models.UserFavorite import UserFavorite
