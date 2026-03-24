from datetime import date
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# ПРОГНОЗЫ (Forecast Schemas)
# =============================================================================

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


class ForecastEntry(BaseModel):
    """Запись прогноза для временного ряда."""
    dt: date = Field(..., description="Дата прогноза")
    predicted_sales: float = Field(..., ge=0, description="Прогноз продаж")
    model_version: str = Field(..., description="Версия модели")


class ProductForecast(BaseModel):
    """Прогноз по конкретному товару."""
    product_id: int = Field(..., ge=1, description="ID товара")
    product_name: Optional[str] = Field(None, description="Название товара")
    brand: Optional[str] = Field(None, description="Бренд")
    latest_prediction: Optional[PredictionDetail] = Field(None, description="Последний прогноз")
    forecast_history: List[ForecastEntry] = Field(default_factory=list, description="История прогнозов")


class ProductForecastsResponse(BaseModel):
    """Ответ для get_product_forecasts — прогнозы по всем товарам."""
    data: List[ProductForecast] = Field(..., description="Список прогнозов по товарам")

    model_config = ConfigDict(from_attributes=True)


class ForecastHistoryResponse(BaseModel):
    """Ответ для get_forecast_history — история прогнозов."""
    product_id: int = Field(..., ge=1, description="ID товара")
    data: List[ForecastEntry] = Field(..., description="Временной ряд прогнозов")

    model_config = ConfigDict(from_attributes=True)


class ForecastSummaryItem(BaseModel):
    """Сводка по одному товару."""
    product_id: int = Field(..., ge=1, description="ID товара")
    product_name: Optional[str] = Field(None, description="Название товара")
    predicted_sales: float = Field(..., ge=0, description="Прогноз продаж")
    days_to_oos: Optional[float] = Field(None, ge=0, description="Дней до обнуления")
    is_oos_risk: bool = Field(..., description="Флаг риска out-of-stock")


class ForecastSummaryResponse(BaseModel):
    """Общая сводка по прогнозам."""
    total_products: int = Field(..., ge=0, description="Количество товаров с прогнозом")
    avg_predicted_sales: float = Field(..., ge=0, description="Средний прогноз продаж")
    total_predicted_revenue: float = Field(..., ge=0, description="Прогнозируемая выручка")
    oos_risk_count: int = Field(..., ge=0, description="Товары с риском out-of-stock")
    items: List[ForecastSummaryItem] = Field(default_factory=list, description="Детализация по товарам")

    model_config = ConfigDict(from_attributes=True)