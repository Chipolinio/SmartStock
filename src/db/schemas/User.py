from typing import Annotated, Optional
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from pydantic import field_validator, StrictInt

from src.utils.validators import validate_email_strict


class UserRole(str, Enum):
    USER = "user"
    PRO = "pro"
    ADMIN = "admin"


class UserBase(BaseModel):
    user_id: Annotated[int, Field(
        default=None,
        gt=0,
        description="Внешний ID (например, Telegram ID)",
        examples=[555666777]
    )] = None
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
    is_active: Annotated[bool, Field(
        True,
        description="Статус активности пользователя"
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
    created_at: Annotated[datetime, Field(
        ...,
        description="Дата регистрации"
    )]

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """Ответ профиля пользователя - только то, что можно изменить."""
    email: Annotated[EmailStr, Field(
        ...,
        min_length=5,
        max_length=50,
        description="Электронная почта пользователя",
        examples=["user@example.com"]
    )]

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    email: Annotated[Optional[EmailStr], Field(
        None,
        description="Электронная почта"
    )]
    password: Annotated[Optional[str], Field(
        None,
        min_length=8,
        max_length=100,
        description="Новый пароль"
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


class UserLogin(BaseModel):
    email: Annotated[EmailStr, Field(
        ...,
        description="Электронная почта пользователя"
    )]
    password: Annotated[str, Field(
        ...,
        min_length=8,
        max_length=100,
        description="Пароль"
    )]

    model_config = ConfigDict(str_strip_whitespace=True)