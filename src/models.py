from sqlalchemy import (
    Column, Integer, BigInteger, Text, Boolean,
    Numeric, Date, DateTime, ForeignKey, Index, func
)
from sqlalchemy.orm import relationship
from src.db.database import Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    product_id = Column(BigInteger, nullable=False, unique=True)
    name = Column(Text, nullable=False)
    brand = Column(Text)
    subject = Column(Text)
    entity = Column(Text)

    # Relationships
    prices = relationship("PriceTS", back_populates="product", cascade="all, delete-orphan")
    stocks = relationship("StockTS", back_populates="product", cascade="all, delete-orphan")
    socials = relationship("SocialTS", back_populates="product", cascade="all, delete-orphan")
    deliveries = relationship("DeliveryTS", back_populates="product", cascade="all, delete-orphan")
    sales_proxies = relationship("SalesProxyTS", back_populates="product", cascade="all, delete-orphan")
    features = relationship("ProductFeaturesDaily", back_populates="product", cascade="all, delete-orphan")
    predictions = relationship("PredictedSalesTS", back_populates="product", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, unique=True)
    email = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    is_pro = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())

class PriceTS(Base):
    __tablename__ = "prices_ts"
    id = Column(Integer, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    dt = Column(Date, nullable=False)
    price_sale = Column(Integer, nullable=False)
    discount_pct = Column(Numeric(5, 2))
    product = relationship("Product", back_populates="prices")
    __table_args__ = (Index("idx_prices_dt", "dt"),)

class StockTS(Base):
    __tablename__ = "stock_ts"
    id = Column(Integer, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    dt = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    product = relationship("Product", back_populates="stocks")
    __table_args__ = (Index("idx_stock_dt", "dt"),)

class SocialTS(Base):
    __tablename__ = "social_ts"
    id = Column(Integer, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    dt = Column(Date, nullable=False)
    rating = Column(Numeric(3, 2))
    feedbacks = Column(Integer)
    product = relationship("Product", back_populates="socials")

class DeliveryTS(Base):
    __tablename__ = "delivery_ts"
    id = Column(Integer, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    dt = Column(Date, nullable=False)
    delivery_days = Column(Integer)
    product = relationship("Product", back_populates="deliveries")

class SalesProxyTS(Base):
    __tablename__ = "sales_proxy_ts"
    id = Column(Integer, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    dt = Column(Date, nullable=False)
    sales = Column(Integer, nullable=False)
    confidence = Column(Numeric(3, 2))
    product = relationship("Product", back_populates="sales_proxies")
    __table_args__ = (Index("idx_sales_proxy_dt", "dt"),)

class ProductFeaturesDaily(Base):
    __tablename__ = "product_features_daily"
    id = Column(Integer, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    dt = Column(Date, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    discount_pct = Column(Numeric(5, 2))
    rating = Column(Numeric(3, 2))
    feedbacks = Column(Integer)
    avg_sales_7d = Column(Numeric(12, 2))
    avg_sales_14d = Column(Numeric(12, 2))
    stock_left = Column(Integer, nullable=False)
    days_to_oos = Column(Numeric(10, 2))
    price_rank_in_category = Column(Integer)
    rating_rank_in_category = Column(Integer)
    product = relationship("Product", back_populates="features")
    __table_args__ = (Index("idx_features_dt", "dt"),)

class PredictedSalesTS(Base):
    __tablename__ = "predicted_sales_ts"
    id = Column(Integer, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    dt = Column(Date, nullable=False)
    predicted_sales = Column(Numeric(12, 2), nullable=False)
    model_version = Column(Text, nullable=False)
    product = relationship("Product", back_populates="predictions")

class UserFavorite(Base):
    __tablename__ = "user_favorites"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.product_id"), nullable=False)
    added_at = Column(Date, nullable=False, server_default=func.current_date())