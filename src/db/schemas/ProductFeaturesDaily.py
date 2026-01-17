from typing import Annotated, Optional
from pydantic import Field, StrictInt, ConfigDict
from .BaseTS import BaseTS


class ProductFeaturesDailyBase(BaseTS):
    price: Annotated[float, Field(..., ge=0, description="Цена на момент замера")]
    discount_pct: Annotated[Optional[float], Field(None, ge=0, le=100)]
    rating: Annotated[Optional[float], Field(None, ge=0, le=5)]
    feedbacks: Annotated[Optional[int], Field(None, ge=0)]
    avg_sales_7d: Annotated[Optional[float], Field(None, ge=0)]
    avg_sales_14d: Annotated[Optional[float], Field(None, ge=0)]
    stock_left: Annotated[int, Field(..., ge=0)]
    days_to_oos: Annotated[Optional[float], Field(None, ge=0, description="Дней до обнуления склада")]
    price_rank_in_category: Annotated[Optional[int], Field(None, ge=1)]
    rating_rank_in_category: Annotated[Optional[int], Field(None, ge=1)]


class ProductFeaturesDailyCreate(ProductFeaturesDailyBase):
    pass


class ProductFeaturesDailyResponse(ProductFeaturesDailyBase):
    id: Annotated[StrictInt, Field(..., ge=1)]

    model_config = ConfigDict(from_attributes=True)