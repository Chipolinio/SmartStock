import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories import UserRepositories as UserRepo
from src.db.repositories import UserFavoriteRepositories as FavRepo
from src.db.schemas.UserFavorite import UserFavoriteCreate, UserFavoriteResponse
from src.db.schemas.Product import ProductResponse

logger = logging.getLogger(__name__)


async def get_user(user_id: int, session: AsyncSession):
    user = await UserRepo.read_user_by_id(user_id, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден."
        )
    return user

async def link_tg_id_to_user(email: str, tg_id: int, session: AsyncSession):

    existing_user = await UserRepo.read_user_by_id(tg_id, session)
    if existing_user:
        raise HTTPException(status_code=409, detail="Этот Telegram ID уже занят")

    success = await UserRepo.update_user_tg_id(email, tg_id, session)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь с таким email не найден")

    return {"status": "success", "message": f"ID {tg_id} привязан к {email}"}


async def create_user_favorites(
        favorite_in: UserFavoriteCreate,
        session: AsyncSession
) -> UserFavoriteResponse:
    await get_user(favorite_in.user_id, session)

    product_exists = await FavRepo.check_product_exists(
        product_id=favorite_in.product_id,
        session=session
    )
    if not product_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар {favorite_in.product_id} не найден в системе."
        )

    favorite_from_db = await FavRepo.create_user_favorites(
        fav_in=favorite_in,
        session=session
    )

    if favorite_from_db is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Этот товар уже находится в вашем списке избранного"
        )

    await session.commit()
    return UserFavoriteResponse.model_validate(favorite_from_db)


async def read_user_favorites(
        user_id: int,
        session: AsyncSession
) -> List[ProductResponse]:
    await get_user(user_id, session)

    products_models = await FavRepo.read_user_favorites(
        user_id=user_id,
        session=session
    )
    return [ProductResponse.model_validate(p) for p in products_models]


async def delete_user_favorites(
        user_id: int,
        product_id: int,
        session: AsyncSession
):
    await get_user(user_id, session)

    await FavRepo.delete_user_favorites(
        user_id=user_id,
        product_id=product_id,
        session=session
    )
    return {"detail": "Товар удален из избранного"}