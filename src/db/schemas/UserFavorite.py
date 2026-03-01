from typing import Annotated, List
from pydantic import BaseModel, Field, ConfigDict, StrictInt
from datetime import date

class UserFavoriteBase(BaseModel):
    user_id: Annotated[int, Field(..., gt=0, description="ID пользователя")]
    product_id: Annotated[int, Field(..., gt=0, description="Артикул товара")]

class UserFavoriteCreateRequest(BaseModel):
    product_id: Annotated[int, Field(..., gt=0, description="Артикул товара")]

class UserFavoriteBatchRequest(BaseModel):
    product_ids: List[int]

class UserFavoriteCreate(UserFavoriteBase):
    pass

class UserFavoriteResponse(UserFavoriteBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID связи")]
    added_at: Annotated[date, Field(..., description="Дата добавления")]

    model_config = ConfigDict(from_attributes=True)