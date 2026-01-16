from typing import Annotated, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from pydantic import field_validator, StrictStr, StrictInt

from .validators import validate_email_strict


class UserRole(str, Enum):
    USER = "user"
    PRO = "pro"
    ADMIN = "admin"


class UserBase(BaseModel):
    user_id: Annotated[int, Field(
        ...,
        gt=0,
        description="Внешний ID (например, Telegram ID)",
        examples=[555666777]
    )]
    email: Annotated[EmailStr, Field(
        ...,
        min_length=5,
        max_length=50,
        description="Электронная почта пользователя",
        examples=["user@example.com"]
    )]
    role: Annotated[UserRole, Field(
        UserRole.USER,
        description="Роль пользователя в системе"
    )]
    is_pro: Annotated[bool, Field(
        False,
        description="Статус подписки PRO"
    )]

    model_config = ConfigDict(str_strip_whitespace=True)


class UserCreate(UserBase):
    password: Annotated[str, Field(
        ...,
        min_length=8,
        max_length=100,
        description="Пароль в hash"
    )]


class UserResponse(UserBase):
    id: Annotated[StrictInt, Field(
        ...,
        ge=1,
        description="Внутренний ID записи в БД (из Base)"
    )]

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    user_id: Annotated[Optional[int], Field(
        None,
        gt=0,
        description="Внешний ID"
    )]
    email: Annotated[Optional[EmailStr], Field(
        None,
        description="Электронная почта"
    )]
    role: Annotated[Optional[UserRole], Field(
        None,
        description="Роль пользователя"
    )]
    is_pro: Annotated[Optional[bool], Field(
        None,
        description="Статус подписки PRO"
    )]

    @field_validator("email", mode="after")
    @classmethod
    def check_email(cls, v):
        if v:
            return validate_email_strict(v)
        return v

    model_config = ConfigDict(str_strip_whitespace=True)


class UserInDB(UserResponse):
    password_hash: Annotated[str, Field(
        ...,
        description="хэш пароль из колонки password_hash"
    )]