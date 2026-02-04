from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.repositories import UserFavoriteRepositories
from src.db.schemas.UserFavorite import UserFavoriteCreate, UserFavoriteResponse
from src.db.schemas.Product import ProductResponse


async def create_user_favorites(
        favorite_in: UserFavoriteCreate,
        session: AsyncSession
) -> UserFavoriteResponse:
    product_exists = await UserFavoriteRepositories.check_product_exists(
        product_id=favorite_in.product_id,
        session=session
    )
    if not product_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Товар с артикулом {favorite_in.product_id} не найден в базе. "
                   f"Сначала добавьте его в систему."
        )

    favorite_from_db = await UserFavoriteRepositories.create_user_favorites(
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
    products_models = await UserFavoriteRepositories.read_user_favorites(
        user_id=user_id,
        session=session
    )
    return [ProductResponse.model_validate(p) for p in products_models]

async def delete_user_favorites(
        user_id: int,
        product_id: int,
        session: AsyncSession
):
    await UserFavoriteRepositories.delete_user_favorites(
        user_id=user_id,
        product_id=product_id,
        session=session
    )
    return {"detail": "Товар удален из избранного"}