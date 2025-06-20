from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import Column, Integer, String, Date, Float

load_dotenv()
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "smartstock")
# URL подключения к базе
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Sales(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    product_id = Column(Integer, index=True)
    product_name = Column(String, index=True)
    quantity = Column(Integer)
    revenue = Column(Float)
    store_id = Column(Integer, index=True)

class Forecasts(Base):
    __tablename__ = "forecasts"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    product_id = Column(Integer, index=True)
    product_name = Column(String, index=True)
    predicted_quantity = Column(Float, index=True)
    confidence = Column(Float, index=True)
    forecast_method = Column(String, default="simple_average")
    created_ad = Column(Date, default=lambda: date.today())

# Создание таблиц
Base.metadata.create_all(bind=engine)

# Функция для получения сессии
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()