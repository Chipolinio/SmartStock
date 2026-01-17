from typing import Annotated
from pydantic import  Field, ConfigDict, StrictInt

from .BaseTS import BaseTS

class PriceTSBase(BaseTS):
    price_sale: Annotated[int, Field(..., ge=0, description="Цена")]
    discount_pct: Annotated[float, Field(0, ge=0, le=100)]

class PriceTSCreate(PriceTSBase):
    pass

class PriceTSResponse(PriceTSBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID")]

    model_config = ConfigDict(from_attributes=True)