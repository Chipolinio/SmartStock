import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories import UserRepositories as UserRepo
from src.db.repositories import UserFavoriteRepositories as FavRepo
from src.db.schemas.UserFavorite import UserFavoriteCreate, UserFavoriteResponse
from src.db.schemas.Product import ProductResponse

logger = logging.getLogger(__name__)

async def _get_db_user_by_internal_id(internal_id: int, session: AsyncSession):
    user = await UserRepo.read_user_by_internal_id(internal_id, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user

async def link_user_telegram(internal_id: int, tg_id: int, session: AsyncSession):
    user = await _get_db_user_by_internal_id(internal_id, session)
    success = await UserRepo.update_user_tg_id(user.email, tg_id, session)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка обновления БД")
    await session.commit()
    return {"status": "success", "message": "Telegram привязан"}

async def read_user_favorites(internal_id: int, session: AsyncSession) -> List[ProductResponse]:
    user = await _get_db_user_by_internal_id(internal_id, session)
    if not user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram не привязан")

    products = await FavRepo.read_user_favorites(user_id=user.user_id, session=session)
    return [ProductResponse.model_validate(p) for p in products]

async def create_user_favorites(internal_id: int, product_id: int, session: AsyncSession):
    user = await _get_db_user_by_internal_id(internal_id, session)
    if not user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Сначала привяжите Telegram")

    favorite_in = UserFavoriteCreate(user_id=user.user_id, product_id=product_id)

    if not await FavRepo.check_product_exists(product_id, session):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")

    res = await FavRepo.create_user_favorites(favorite_in, session)
    if not res:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Уже в избранном")

    await session.commit()
    return UserFavoriteResponse.model_validate(res)


async def create_batch_favorites(internal_id: int, product_ids: List[int], session: AsyncSession):
    user = await _get_db_user_by_internal_id(internal_id, session)

    if not user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала привяжите Telegram в личном кабинете."
        )

    await FavRepo.create_batch_favorites(
        user_id=user.user_id,
        product_ids=product_ids,
        session=session
    )

    await session.commit()

    return {"status": "success", "message": f"Добавлено товаров: {len(product_ids)}"}

async def delete_user_favorites(internal_id: int, product_id: int, session: AsyncSession):
    user = await _get_db_user_by_internal_id(internal_id, session)
    if not user.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram не привязан")

    await FavRepo.delete_user_favorites(user_id=user.user_id, product_id=product_id, session=session)
    await session.commit()