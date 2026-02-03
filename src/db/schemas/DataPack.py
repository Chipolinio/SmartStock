from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from src.db.schemas.StockTS import StockTSCreate
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate
from src.db.schemas.PriceTS import PriceTSCreate
from src.db.schemas.DeliveryTS import DeliveryTSCreate
from src.db.schemas.SocialTS import SocialTSCreate

class FullPayload(BaseModel):
    stocks: Annotated[List[StockTSCreate], Field(
        ...,
        description="Список данных по остаткам (timeseries)"
    )]
    prices: Annotated[List[PriceTSCreate], Field(
        ...,
        description="Список данных по ценам"
    )]
    deliveries: Annotated[List[DeliveryTSCreate], Field(
        ...,
        description="Данные по срокам доставки"
    )]
    socials: Annotated[List[SocialTSCreate], Field(
        ...,
        description="Социальные метрики (рейтинг, отзывы)"
    )]
    sales: Annotated[Optional[List[SalesProxyTSCreate]], Field(
        None,
        description="Опциональный список зафиксированных продаж"
    )]

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True
    )