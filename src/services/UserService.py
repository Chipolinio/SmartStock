import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.UserRepositories import read_user_by_internal_id, read_user_by_email, update_user
from src.db.repositories.UserFavoriteRepositories import (
    read_user_favorites as repo_read_user_favorites,
    check_product_exists,
    create_user_favorites as repo_create_user_favorites,
    create_batch_favorites as repo_create_batch_favorites,
    delete_user_favorites as repo_delete_user_favorites
)
from src.db.schemas.UserFavorite import UserFavoriteCreate, UserFavoriteResponse
from src.db.schemas.Product import ProductResponse

logger = logging.getLogger(__name__)

async def _get_db_user_by_internal_id(internal_id: int, session: AsyncSession):
    user = await read_user_by_internal_id(internal_id, session)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user

async def link_user_telegram(internal_id: int, tg_id: int, session: AsyncSession):
    user = await _get_db_user_by_internal_id(internal_id, session)
    from src.db.repositories.UserFavoriteRepositories import update_user_tg_id
    success = await update_user_tg_id(user.email, tg_id, session)
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка обновления БД")
    await session.commit()
    return {"status": "success", "message": "Telegram привязан"}

async def read_user_favorites(internal_id: int, session: AsyncSession) -> List[ProductResponse]:
    """Получить избранные товары пользователя."""
    user = await _get_db_user_by_internal_id(internal_id, session)
    
    # Используем внутренний user.id для поиска избранного
    products = await repo_read_user_favorites(user_id=user.id, session=session)
    return [ProductResponse.model_validate(p) for p in products]

async def create_user_favorites(internal_id: int, product_id: int, session: AsyncSession):
    """Добавить товар в избранное."""
    user = await _get_db_user_by_internal_id(internal_id, session)

    # Используем внутренний user.id для избранного
    favorite_in = UserFavoriteCreate(user_id=user.id, product_id=product_id)

    if not await check_product_exists(product_id, session):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")

    res = await repo_create_user_favorites(favorite_in, session)
    if not res:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Уже в избранном")

    await session.commit()
    return UserFavoriteResponse.model_validate(res)


async def create_batch_favorites(internal_id: int, product_ids: List[int], session: AsyncSession):
    """
    Массовое добавление товаров в избранное.
    
    Если товара нет в БД — создаётся заглушка.
    """
    from src.services.Seeder import seed_articles_batch
    
    user = await _get_db_user_by_internal_id(internal_id, session)
    
    # Проверяем, какие товары есть в БД
    from src.db.repositories.ProductRepositories import get_by_article
    missing_articles = []
    
    for product_id in product_ids:
        product = await get_by_article(product_id, session)
        if not product:
            missing_articles.append(product_id)
    
    # Создаём заглушки для отсутствующих товаров
    if missing_articles:
        logger.info(f"Creating stubs for {len(missing_articles)} products...")
        await seed_articles_batch(missing_articles, session)
    
    # Добавляем все товары в избранное
    await repo_create_batch_favorites(
        user_id=user.id,
        product_ids=product_ids,
        session=session
    )

    await session.commit()

    return {
        "status": "success",
        "message": f"Добавлено товаров: {len(product_ids)}",
        "created_stubs": len(missing_articles)
    }

async def delete_user_favorites(internal_id: int, product_id: int, session: AsyncSession):
    """Удалить товар из избранного."""
    user = await _get_db_user_by_internal_id(internal_id, session)

    # Используем внутренний user.id для избранного
    await repo_delete_user_favorites(user_id=user.id, product_id=product_id, session=session)
    await session.commit()