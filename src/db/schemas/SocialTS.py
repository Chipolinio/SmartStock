from typing import Annotated
from pydantic import  Field, ConfigDict, StrictInt

from .BaseTS import BaseTS

class SocialTSBase(BaseTS):
    rating: Annotated[float, Field(..., ge=0, description="Рейтинг")]
    feedbacks: Annotated[int, Field(..., ge=0, description="Отзывы")]

class SocialTSCreate(SocialTSBase):
    pass

class SocialTSResponse(SocialTSBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID")]

    model_config = ConfigDict(from_attributes=True)