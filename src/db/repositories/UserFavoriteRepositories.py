from sqlalchemy import select, delete, join
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from src.db.models import UserFavorite, Product
from src.db.schemas.UserFavorite import UserFavoriteCreate

async def create_user_favorites(
        fav_in: UserFavoriteCreate,
        session: AsyncSession
) -> UserFavorite | None:
    check_stmt = select(UserFavorite).where(
        UserFavorite.user_id == fav_in.user_id,
        UserFavorite.product_id == fav_in.product_id
    )
    result = await session.execute(check_stmt)
    if result.scalar_one_or_none():
        return None

    db_fav = UserFavorite(**fav_in.model_dump())
    session.add(db_fav)
    await session.commit()
    await session.refresh(db_fav)
    return db_fav

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
    return list(result.scalars().all())


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