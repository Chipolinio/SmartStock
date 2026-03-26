from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import date


class MLInputSchema(BaseModel):
    """
    Схема валидации входных данных для ML-модели.
    Проверяет на Null и аномалии.
    """
    product_id: int = Field(..., gt=0, description="ID товара")
    price: float = Field(..., gt=0, le=500000, description="Цена товара")
    discount_pct: float = Field(default=0, ge=0, le=100, description="Процент скидки")
    rating: float = Field(default=0, ge=0, le=5, description="Рейтинг товара")
    feedbacks: int = Field(default=0, ge=0, description="Количество отзывов")
    stock_left: int = Field(..., ge=0, description="Остаток на складе")
    price_rank_in_category: Optional[int] = Field(default=None, ge=1, description="Ранг цены в категории")
    
    @field_validator("price")
    @classmethod
    def check_price_anomaly(cls, v: float) -> float:
        """Проверка цены на аномалии."""
        if v < 1:
            raise ValueError("Цена не может быть меньше 1 рубля")
        if v > 100000:
            # Предупреждение о высокой цене (не блокирующая валидация)
            pass
        return v
    
    @field_validator("feedbacks")
    @classmethod
    def check_feedbacks_anomaly(cls, v: int) -> int:
        """Проверка отзывов на накрутку."""
        # Увеличили лимит до 1 млн — популярные товары могут иметь 200k+ отзывов
        if v > 1_000_000:
            raise ValueError("Аномальное количество отзывов (возможна накрутка)")
        return v
    
    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "example": {
                "product_id": 12345678,
                "price": 1999.99,
                "discount_pct": 15.0,
                "rating": 4.8,
                "feedbacks": 1250,
                "stock_left": 500,
                "price_rank_in_category": 5
            }
        }
    }


class MLBatchInputSchema(BaseModel):
    """Схема для пакетной валидации данных."""
    products: List[MLInputSchema] = Field(..., min_length=1, max_length=1000)
