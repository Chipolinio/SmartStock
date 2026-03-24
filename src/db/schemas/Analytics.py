from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import date

from src.db.schemas.DashboardMetric import (
    SalesHistoryResponse,
    StockDynamicsResponse,
    ABCAnalysisResponse,
    XYZAnalysisResponse,
    TopProductsByRevenueResponse,
    TopProductsBySalesResponse,
    ProductsRatingResponse,
    DashboardKPIResponse
)

# =============================================================================
# УНИВЕРСАЛЬНАЯ АНАЛИТИКА (для /analytics/aggregate)
# =============================================================================

DimensionType = Literal["dt", "brand", "subject", "product_id"]
MetricType = Literal["revenue", "sales", "rating", "abc", "xyz", "score", "recommendation"]


class AnalyticsMetrics(BaseModel):
    revenue: Optional[float] = None
    sales: Optional[int] = None
    abc: Optional[str] = None
    xyz: Optional[str] = None
    score: Optional[float] = None
    avg_rating: Optional[float] = None


class AnalyticsEntry(BaseModel):
    dimensions: Dict[DimensionType, Any]
    metrics: AnalyticsMetrics
    recommendation: Optional[str] = None


class AnalyticsRequest(BaseModel):
    date_from: date
    date_to: date
    dimensions: List[DimensionType] = Field(..., min_length=1)
    metrics: List[MetricType] = Field(..., min_length=1)
    filters: Optional[Dict[str, List[Any]]] = Field(default_factory=dict)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date_from": "2026-02-01",
                "date_to": "2026-02-06",
                "dimensions": ["subject"],
                "metrics": ["revenue", "sales", "abc"],
                "filters": {}
            }
        }
    )


class AnalyticsResponse(BaseModel):
    status: str = "success"
    data: List[AnalyticsEntry]
    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# DASHBOARD BASE REQUEST (для /dashboard/*)
# =============================================================================

class DashboardBaseRequest(BaseModel):
    """Базовый запрос для дашборда."""
    days: int = Field(default=30, ge=1, le=365, description="Период в днях")
    product_id: Optional[int] = Field(None, gt=0, description="Фильтр по товару")
    brand: Optional[str] = Field(None, description="Фильтр по бренду")
    subject: Optional[str] = Field(None, description="Фильтр по категории")

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# СХЕМЫ ДЛЯ DASHBOARD (используются в /dashboard/*)
# =============================================================================
# Эти классы — алиасы на схемы из DashboardMetric для удобства импорта

# SalesDynamicsResponse уже определён как SalesHistoryResponse в DashboardMetric
# StockDynamicsResponse уже определён как StockDynamicsResponse в DashboardMetric
# ABCAnalysisResponse уже определён как ABCAnalysisResponse в DashboardMetric
# и т.д.

