from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, StrictInt
from datetime import date

class UserFavoriteBase(BaseModel):
    user_id: Annotated[int, Field(..., gt=0, description="ID пользователя")]
    product_id: Annotated[int, Field(..., gt=0, description="Артикул товара")]

class UserFavoriteCreate(UserFavoriteBase):
    pass

class UserFavoriteResponse(UserFavoriteBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID связи")]
    added_at: Annotated[date, Field(..., description="Дата добавления")]

    model_config = ConfigDict(from_attributes=True)