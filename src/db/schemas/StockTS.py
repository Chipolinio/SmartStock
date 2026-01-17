from typing import Annotated
from pydantic import  Field, ConfigDict, StrictInt

from .BaseTS import BaseTS

class StockSBase(BaseTS):
    quantity: Annotated[int, Field(..., ge=0, description="Количество")]

class StockTSCreate(StockSBase):
    pass

class StockTSResponse(StockSBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID")]

    model_config = ConfigDict(from_attributes=True)