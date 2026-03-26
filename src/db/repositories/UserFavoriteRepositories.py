from sqlalchemy import select, delete, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, List, Optional
from sqlalchemy.orm import aliased

from src.db.models.UserFavorite import UserFavorite
from src.db.models.Product import Product
from src.db.models.PriceTS import PriceTS
from src.db.models.StockTS import StockTS
from src.db.schemas.UserFavorite import UserFavoriteCreate


async def create_user_favorites(fav_in: UserFavoriteCreate, session: AsyncSession) -> UserFavorite | None:
    check_stmt = select(UserFavorite).where(
        UserFavorite.user_id == fav_in.user_id,
        UserFavorite.product_id == fav_in.product_id
    )
    result = await session.execute(check_stmt)
    if result.scalars().first():
        return None

    db_fav = UserFavorite(**fav_in.model_dump())
    session.add(db_fav)
    await session.flush()
    return db_fav


async def create_batch_favorites(user_id: int, product_ids: List[int], session: AsyncSession):
    for p_id in product_ids:
        stmt = select(UserFavorite).where(UserFavorite.user_id == user_id, UserFavorite.product_id == p_id)
        exists_res = await session.execute(stmt)
        if not exists_res.scalars().first():
            session.add(UserFavorite(user_id=user_id, product_id=p_id))
    await session.flush()


async def check_product_exists(product_id: int, session: AsyncSession) -> bool:
    stmt = select(exists().where(Product.product_id == product_id))
    result = await session.execute(stmt)
    return result.scalar()


async def read_user_favorites(user_id: int, session: AsyncSession) -> Sequence[Product]:
    """
    Получить избранные товары пользователя.
    Без eager loading чтобы не триггерить relationships Product.
    """
    stmt = (
        select(Product)
        .join(UserFavorite)
        .where(UserFavorite.user_id == user_id)
        .order_by(Product.product_id)
    )
    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def read_user_favorites_filtered(
    user_id: int, 
    session: AsyncSession, 
    brand: str = None, 
    subject: str = None
) -> Sequence[Product]:
    """
    Получить избранные товары пользователя с фильтрами по brand и subject.
    """
    conditions = [UserFavorite.user_id == user_id]
    
    if brand:
        conditions.append(Product.brand == brand)
    if subject:
        conditions.append(Product.subject == subject)
    
    stmt = (
        select(Product)
        .join(UserFavorite)
        .where(*conditions)
        .order_by(Product.product_id)
    )
    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def read_user_favorites_with_details(
    user_id: int,
    session: AsyncSession
) -> Sequence[tuple]:
    """
    Получить избранные товары пользователя с ценой и остатком.
    Возвращает кортежи: (Product, price, stock)
    """
    # Подзапросы для получения последней цены и остатка
    latest_price = (
        select(PriceTS.price_sale)
        .where(PriceTS.product_id == Product.product_id)
        .order_by(PriceTS.dt.desc())
        .limit(1)
        .correlate(Product)
        .scalar_subquery()
    )
    
    latest_stock = (
        select(StockTS.quantity)
        .where(StockTS.product_id == Product.product_id)
        .order_by(StockTS.dt.desc())
        .limit(1)
        .correlate(Product)
        .scalar_subquery()
    )
    
    stmt = (
        select(Product, latest_price.label("price"), latest_stock.label("stock"))
        .join(UserFavorite)
        .where(UserFavorite.user_id == user_id)
        .order_by(Product.product_id)
    )
    result = await session.execute(stmt)
    return result.all()


async def delete_user_favorites(user_id: int, product_id: int, session: AsyncSession):
    stmt = delete(UserFavorite).where(UserFavorite.user_id == user_id, UserFavorite.product_id == product_id)
    await session.execute(stmt)
