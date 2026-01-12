from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date, datetime
from typing import Optional, List

class ProductBase(BaseModel):
    product_id: int
    name: str
    brand: Optional[str] = None
    subject: Optional[str] = None
    entity: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    user_id: int
    email: EmailStr
    role: str
    is_pro: bool = False

class UserRead(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PriceCreate(BaseModel):
    product_id: int
    dt: date
    price_sale: int
    discount_pct: Optional[float] = None