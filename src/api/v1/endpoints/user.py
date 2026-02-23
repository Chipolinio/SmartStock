from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_db
from src.db.schemas.UserFavorite import UserFavoriteCreate, UserFavoriteResponse
from src.db.schemas.Product import ProductResponse
from src.services import UserService

router = APIRouter()

@router.post("/favorites", response_model=UserFavoriteResponse, status_code=status.HTTP_201_CREATED)
async def create_favorite_product(
    fav_product: UserFavoriteCreate,
    session: AsyncSession = Depends(get_db)
):
    return await UserService.create_user_favorites(
        favorite_in=fav_product,
        session=session
    )

@router.get("/favorites", response_model=List[ProductResponse], status_code=status.HTTP_200_OK)
async def read_fav_products(
    user_id: int = Query(..., gt=0, description="Telegram ID пользователя"),
    session: AsyncSession = Depends(get_db)
):
    return await UserService.read_user_favorites(
        user_id=user_id,
        session=session
    )

@router.delete("/favorites/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fav_product(
    product_id: int,
    user_id: int = Query(..., gt=0, description="Telegram ID пользователя"),
    session: AsyncSession = Depends(get_db)
):
    await UserService.delete_user_favorites(
        user_id=user_id,
        product_id=product_id,
        session=session
    )
    return None


@router.patch("/link-telegram")
async def link_telegram(
    email: str,
    tg_id: int,
    session: AsyncSession = Depends(get_db)
):
    return await UserService.link_tg_id_to_user(
        email=email,
        tg_id=tg_id,
        session=session
    )