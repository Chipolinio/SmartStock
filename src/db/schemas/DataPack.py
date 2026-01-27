from pydantic import BaseModel
from typing import List, Optional

from src.db.schemas.StockTS import StockTSCreate, StockTSResponse
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate, SalesProxyTSResponse
from src.db.schemas.PriceTS import PriceTSCreate, PriceTSResponse
from src.db.schemas.DeliveryTS import DeliveryTSCreate, DeliveryTSResponse
from src.db.schemas.SocialTS import SocialTSCreate, SocialTSResponse
from src.db.schemas.PredictedSalesTS import PredictedSalesTSCreate, PredictedSalesTSResponse

class FullPayload(BaseModel):
    stocks: List[StockTSCreate]
    prices: List[PriceTSCreate]
    deliveries: List[DeliveryTSCreate]
    socials: List[SocialTSCreate]
    sales: Optional[List[SalesProxyTSCreate]] = None
    predicted_sales: Optional[List[PredictedSalesTSCreate]] = None

    class Config:
        from_attributes = True