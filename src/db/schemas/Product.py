from typing import Annotated, Optional
from pydantic import BaseModel, Field, ConfigDict, StrictInt
from pydantic import field_validator

from src.utils.validators import validate_clean_text

class ProductBase(BaseModel):
    product_id: Annotated[int, Field(
        ...,
        gt=0,
        description="Артикул товара на маркетплейсе",
        examples=[12345678]
    )]
    name: Annotated[str, Field(
        ...,
        min_length=2,
        max_length=200,
        description="Наименование товара",
        examples=["Смартфон Apple iPhone 15"]
    )]
    brand: Annotated[Optional[str], Field(
        None,
        min_length=1,
        max_length=50,
        description="Бренд товара"
    )]
    subject: Annotated[Optional[str], Field(
        None,
        description="Категория (предмет)"
    )]
    entity: Annotated[Optional[str], Field(
        None,
        description="Тип сущности"
    )]

    @field_validator("name", "brand", "subject", "entity", mode="after")
    @classmethod
    def validate_product_strings(cls, v):
        if v is not None:
            return validate_clean_text(v)
        return v

    model_config = ConfigDict(str_strip_whitespace=True)


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID записи в БД")]

    model_config = ConfigDict(from_attributes=True)


class ProductWithDetailsResponse(ProductBase):
    """Расширенный ответ для товара с ценой и остатком."""
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID записи в БД")]
    article: Annotated[StrictInt, Field(..., gt=0, description="Артикул товара (wb_article)")]
    price: Annotated[Optional[float], Field(None, ge=0, description="Текущая цена")]
    stock: Annotated[Optional[int], Field(None, ge=0, description="Текущий остаток")]

    model_config = ConfigDict(from_attributes=True)


class ProductDetailedResponse(ProductBase):
    """Полный ответ для страницы аналитики товара."""
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID записи в БД")]
    article: Annotated[StrictInt, Field(..., gt=0, description="Артикул товара")]
    
    # Текущие метрики
    price: Annotated[Optional[float], Field(None, ge=0, description="Текущая цена")]
    stock: Annotated[Optional[int], Field(None, ge=0, description="Текущий остаток")]
    avg_daily_sales: Annotated[Optional[float], Field(None, ge=0, description="Средние продажи в день (30 дней)")]
    days_to_oos: Annotated[Optional[int], Field(None, ge=0, description="Дней до обнуления склада")]
    
    # Соц. метрики
    rating: Annotated[Optional[float], Field(None, ge=0, le=5, description="Текущий рейтинг")]
    reviews_count: Annotated[Optional[int], Field(None, ge=0, description="Количество отзывов")]
    questions_count: Annotated[Optional[int], Field(None, ge=0, description="Количество вопросов")]
    likes: Annotated[Optional[int], Field(None, ge=0, description="Количество лайков")]
    
    # Статистика
    total_sales: Annotated[Optional[int], Field(None, ge=0, description="Всего продаж")]
    total_revenue: Annotated[Optional[float], Field(None, ge=0, description="Общая выручка")]

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(BaseModel):
    product_id: Annotated[Optional[int], Field(
        None,
        gt=0
    )]
    name: Annotated[Optional[str], Field(
        None,
        min_length=2,
        max_length=200
    )]
    brand: Annotated[Optional[str], Field(
        None,
        min_length=1,
        max_length=50
    )]
    subject: Annotated[Optional[str], Field(None)]
    entity: Annotated[Optional[str], Field(None)]

    @field_validator("name", "brand", "subject", "entity", mode="after")
    @classmethod
    def validate_update_strings(cls, v):
        if v:
            return validate_clean_text(v)
        return v