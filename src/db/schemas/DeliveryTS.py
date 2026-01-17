from typing import Annotated
from pydantic import  Field, ConfigDict, StrictInt

from .BaseTS import BaseTS

class DeliveryTSBase(BaseTS):
    delivery_days: Annotated[int, Field(..., ge=0, description="Доставка")]

class DeliveryTSCreate(DeliveryTSBase):
    pass

class DeliveryTSResponse(DeliveryTSBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID")]

    model_config = ConfigDict(from_attributes=True)