from typing import Annotated, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from src.db.schemas.Product import ProductUpdate
from src.db.schemas.StockTS import StockTSCreate
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate
from src.db.schemas.PriceTS import PriceTSCreate
from src.db.schemas.DeliveryTS import DeliveryTSCreate
from src.db.schemas.SocialTS import SocialTSCreate


class FullPayload(BaseModel):
    products_update: Annotated[Optional[List[ProductUpdate]], Field(
        None, description="Данные для обновления метаданных товаров (категории, бренды)"
    )]
    stocks: Annotated[List[StockTSCreate], Field(..., description="Список данных по остаткам")]
    prices: Annotated[List[PriceTSCreate], Field(..., description="Список данных по ценам")]
    deliveries: Annotated[List[DeliveryTSCreate], Field(..., description="Сроки доставки")]
    socials: Annotated[List[SocialTSCreate], Field(..., description="Рейтинг, отзывы")]
    sales: Annotated[Optional[List[SalesProxyTSCreate]], Field(None)]

    model_config = ConfigDict(from_attributes=True)