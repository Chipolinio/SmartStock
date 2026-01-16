from sqlalchemy import select, delete, join
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from src.db.models import UserFavorite, Product

async def create_user_favorites(
        user_id: int,
        product_id: int,
        session: AsyncSession
) -> UserFavorite | None:
    check_stmt = select(UserFavorite).where(
        UserFavorite.user_id == user_id,
        UserFavorite.product_id == product_id
    )
    existing = await session.execute(check_stmt)
    if existing.scalar_one_or_none():
        return None

    new_fav = UserFavorite(user_id=user_id, product_id=product_id)
    session.add(new_fav)
    await session.commit()
    await session.refresh(new_fav)
    return new_fav

async def read_user_favorites(
        user_id: int,
        session: AsyncSession
) -> Sequence[Product]:
    stmt = (
        select(Product)
        .join(UserFavorite)
        .where(UserFavorite.user_id == user_id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_user_favorites(
        user_id: int,
        product_id: int,
        session: AsyncSession
):
    stmt = (
        delete(UserFavorite)
        .where(UserFavorite.user_id == user_id)
        .where(UserFavorite.product_id == product_id)
    )
    await session.execute(stmt)
    await session.commit()