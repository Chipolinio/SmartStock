from pydantic import BaseModel, validator
from datetime import date
from typing import Optional

class SaleBase(BaseModel):
    date: date
    product_id: int
    product_name: str
    quantity:int
    revenue:float
    store_id: int

class SaleCreate(SaleBase):
    @validator("quantity", "revenue")
    def positive_values(cls, v):
        if v<0:
            raise ValueError("Не может быть отрицательным")
        return v

    class Config:
        json_schema_extra = {  # Изменено с schema_extra
            "example": {
                "date": "2025-06-20",
                "product_id": 1,
                "product_name": "Ноутбук",
                "quantity": 10,
                "revenue": 100.50,
                "store_id": 1
            }
        }
class SaleUpdate(SaleBase):
    quantity: Optional[int] = None
    revenue: Optional[int] = None

class ForecastsBase(BaseModel):
    date: date
    product_id: int
    product_name: str
    predicted_quantity: float
    confidence: float
    forecast_method: str = "simple_average"

class ForecastCreate(ForecastsBase):
    @validator("confidence", )
    def positive_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Должно быть в интервале от 0 до 1")
        return v

    class Config:
        json_schema_extra = {  # Изменено с schema_extra
            "example": {
                "date": "2025-06-21",
                "product_id": 1,
                "product_name": "Ноутбук",
                "predicted_quantity": 15.5,
                "confidence": 0.95,
                "forecast_method": "Простой средний показатель"
            }
        }

class ForecastUpdate(ForecastsBase):
    predicted_quantity: Optional[float] = None
    confidence: Optional[float] = None
    forecast_method: Optional[str] = None