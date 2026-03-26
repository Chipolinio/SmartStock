from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import date


class DashboardMetricSchema(BaseModel):
    """Схема для кастинга результатов агрегации БД во float."""

    product_id: int = Field(..., ge=1, description="ID товара")
    total_sales: Optional[float] = Field(None, description="Общее количество продаж")
    sales_avg: Optional[float] = Field(None, description="Среднее количество продаж")
    sales_std: Optional[float] = Field(None, description="Стандартное отклонение продаж")
    total_revenue: Optional[float] = Field(None, description="Общая выручка")
    avg_rating: Optional[float] = Field(None, description="Средний рейтинг")
    max_feedbacks: Optional[int] = Field(None, ge=0, description="Максимальное количество отзывов")
    avg_delivery: Optional[float] = Field(None, description="Среднее время доставки")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Количество на складе")
    abc_class: Optional[Literal["A", "B", "C"]] = Field(None, description="Класс ABC-анализа")

    model_config = ConfigDict(from_attributes=True)


class SalesHistoryEntry(BaseModel):
    """Запись истории продаж."""

    dt: date = Field(..., description="Дата")
    sales: int = Field(..., ge=0, description="Количество продаж")
    revenue: Optional[float] = Field(None, description="Выручка")

    model_config = ConfigDict(from_attributes=True)


class SalesHistoryResponse(BaseModel):
    """Ответ для get_sales_history."""
    product_id: Optional[int] = Field(None, ge=1, description="ID товара (None для агрегированных данных)")
    data: List[SalesHistoryEntry] = Field(..., description="Временной ряд продаж")

    model_config = ConfigDict(from_attributes=True)


# Алиасы для dashboard.py
SalesDynamicsResponse = SalesHistoryResponse


class StockDynamicsEntry(BaseModel):
    """Запись динамики остатков."""

    dt: date = Field(..., description="Дата")
    quantity: int = Field(..., ge=0, description="Количество на складе")

    model_config = ConfigDict(from_attributes=True)


class StockDynamicsResponse(BaseModel):
    """Ответ для get_stock_dynamics."""
    product_id: Optional[int] = Field(None, ge=1, description="ID товара (None для агрегированных данных)")
    data: List[StockDynamicsEntry] = Field(..., description="Временной ряд остатков")

    model_config = ConfigDict(from_attributes=True)


class ABCAnalysisEntry(BaseModel):
    """Запись ABC-анализа."""

    product_id: int = Field(..., ge=1, description="ID товара")
    product_name: str = Field(..., min_length=1, description="Название товара")
    brand: Optional[str] = Field(None, description="Бренд")
    subject: Optional[str] = Field(None, description="Категория")
    total_revenue: float = Field(..., ge=0, description="Общая выручка")
    revenue_share: float = Field(..., ge=0, le=1, description="Доля выручки")
    abc_class: Literal["A", "B", "C"] = Field(..., description="Класс ABC")

    model_config = ConfigDict(from_attributes=True)


class ABCAnalysisResponse(BaseModel):
    """Ответ для get_abc_data."""
    data: List[ABCAnalysisEntry] = Field(..., description="Список товаров с ABC-классом")

    model_config = ConfigDict(from_attributes=True)


class XYZAnalysisEntry(BaseModel):
    """Запись XYZ-анализа."""

    product_id: int = Field(..., ge=1, description="ID товара")
    product_name: str = Field(..., min_length=1, description="Название товара")
    brand: Optional[str] = Field(None, description="Бренд")
    subject: Optional[str] = Field(None, description="Категория")
    avg_sales: float = Field(..., ge=0, description="Средние продажи")
    sales_std: float = Field(..., ge=0, description="Стандартное отклонение")
    cv: float = Field(..., ge=0, description="Коэффициент вариации")
    xyz_class: Literal["X", "Y", "Z"] = Field(..., description="Класс XYZ")

    model_config = ConfigDict(from_attributes=True)


class XYZAnalysisResponse(BaseModel):
    """Ответ для get_xyz_data."""
    data: List[XYZAnalysisEntry] = Field(..., description="Список товаров с XYZ-классом")

    model_config = ConfigDict(from_attributes=True)


class TopProductEntry(BaseModel):
    """Запись топа товаров."""

    product_id: int = Field(..., ge=1, description="ID товара")
    product_name: str = Field(..., min_length=1, description="Название товара")
    brand: Optional[str] = Field(None, description="Бренд")
    subject: Optional[str] = Field(None, description="Категория")
    total_revenue: float = Field(..., ge=0, description="Общая выручка")
    total_sales: int = Field(..., ge=0, description="Количество продаж")
    rank: int = Field(..., ge=1, description="Позиция в рейтинге")

    model_config = ConfigDict(from_attributes=True)


class TopProductsByRevenueResponse(BaseModel):
    """Ответ для get_top_products_by_revenue."""
    data: List[TopProductEntry] = Field(..., description="Топ товаров по выручке")

    model_config = ConfigDict(from_attributes=True)


class TopProductsBySalesResponse(BaseModel):
    """Ответ для get_top_products_by_sales."""
    data: List[TopProductEntry] = Field(..., description="Топ товаров по продажам")

    model_config = ConfigDict(from_attributes=True)


class ProductsRatingEntry(BaseModel):
    """Запись рейтинга товаров."""

    product_id: int = Field(..., ge=1, description="ID товара")
    product_name: str = Field(..., min_length=1, description="Название товара")
    brand: Optional[str] = Field(None, description="Бренд")
    subject: Optional[str] = Field(None, description="Категория")
    avg_rating: float = Field(..., ge=0, le=5, description="Средний рейтинг")
    feedbacks_count: int = Field(..., ge=0, description="Количество отзывов")
    rank: int = Field(..., ge=1, description="Позиция в рейтинге")

    model_config = ConfigDict(from_attributes=True)


class ProductsRatingResponse(BaseModel):
    """Ответ для get_products_rating."""
    data: List[ProductsRatingEntry] = Field(..., description="Рейтинг товаров")

    model_config = ConfigDict(from_attributes=True)


class DashboardKPIResponse(BaseModel):
    """Ответ для get_dashboard_kpi — общие метрики дашборда."""

    total_revenue: float = Field(..., ge=0, description="Общая выручка")
    total_sales: int = Field(..., ge=0, description="Общее количество продаж")
    avg_rating: float = Field(..., ge=0, le=5, description="Средний рейтинг")
    total_products: int = Field(..., ge=0, description="Количество товаров в избранном")
    avg_delivery_days: Optional[float] = Field(None, ge=0, description="Средняя доставка")
    oos_risk_count: int = Field(..., ge=0, description="Товары с риском out-of-stock")

    model_config = ConfigDict(from_attributes=True)


class LowStockItem(BaseModel):
    """Товар с низким остатком."""

    product_id: int = Field(..., ge=1, description="ID товара")
    product_name: str = Field(..., min_length=1, description="Название товара")
    article: Optional[str] = Field(None, description="Артикул")
    current_stock: int = Field(..., ge=0, description="Текущий остаток")
    avg_sales: float = Field(..., ge=0, description="Средние продажи в день")
    days_until_oos: Optional[float] = Field(None, ge=0, description="Дней до обнуления")
    status: Literal["critical", "warning", "ok"] = Field(..., description="Статус")

    model_config = ConfigDict(from_attributes=True)


class LowStockResponse(BaseModel):
    """Ответ для get_low_stock."""
    data: List[LowStockItem] = Field(..., description="Товары с низким остатком")

    model_config = ConfigDict(from_attributes=True)
