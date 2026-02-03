from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, field_validator

from datetime import date

from src.utils.validators import validate_strict_date


class BaseTS(BaseModel):
    product_id: Annotated[int, Field(
        ...,
        gt=0,
        description="Артикул товара на маркетплейсе",
        examples=[12345678]
    )]
    dt: Annotated[date, Field(
        ...,
        description="Дата замера"
    )]
    @field_validator("dt", mode="after")
    @classmethod
    def check_dt(cls, v) -> date:
        return validate_strict_date(v)

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )