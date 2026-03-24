from typing import Annotated
from pydantic import  Field, ConfigDict, StrictInt

from .BaseTS import BaseTS

class SalesProxyTSBase(BaseTS):
    sales: Annotated[int, Field(..., ge=0, description="Продажи")]
    confidence: Annotated[float, Field(0, ge=0, le=1)]

class SalesProxyTSCreate(SalesProxyTSBase):
    pass

class SalesProxyTSResponse(SalesProxyTSBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID")]

    model_config = ConfigDict(from_attributes=True)