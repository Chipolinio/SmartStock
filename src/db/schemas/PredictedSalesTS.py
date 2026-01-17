from typing import Annotated
from pydantic import  Field, ConfigDict, StrictInt

from .BaseTS import BaseTS

class PredictedTSSalesSBase(BaseTS):
    predicted_sales: Annotated[float, Field(..., ge=0, description="Предсказание продаж")]
    model_version: Annotated[str, Field(..., min_length=1, description="Версия модели")]

class PredictedSalesTSCreate(PredictedTSSalesSBase):
    pass

class PredictedSalesTSResponse(PredictedTSSalesSBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID")]

    model_config = ConfigDict(from_attributes=True)