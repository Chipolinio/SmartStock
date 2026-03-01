from datetime import date
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict

class PredictionDetail(BaseModel):
    sales_next_day: Annotated[float, Field(..., description="Прогноз продаж на следующий день")]
    days_until_out_of_stock: Annotated[float, Field(..., description="Дней до обнуления склада")]
    model_version: str
    dt: date

class StockAlerts(BaseModel):
    is_low_stock: bool = Field(..., description="Флаг: товара меньше чем на неделю")
    critical_oos: bool = Field(..., description="Флаг: товар закончится в ближайшие 3 дня")

class FullForecastResponse(BaseModel):
    product_id: int
    current_stock: int
    current_price: float
    prediction: PredictionDetail
    alerts: StockAlerts

    model_config = ConfigDict(from_attributes=True)