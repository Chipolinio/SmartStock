from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_db
from src.db.schemas.UserFavorite import UserFavoriteCreate, UserFavoriteResponse
from src.db.schemas.Product import ProductResponse
from src.services import FavoriteService

router = APIRouter()

@router.post("/", response_model=UserFavoriteResponse, status_code=status.HTTP_201_CREATED)
async def create_favorite_product(
    fav_product: UserFavoriteCreate,
    session: AsyncSession = Depends(get_db)
):
    return await FavoriteService.create_user_favorites(favorite_in=fav_product, session=session)

@router.get("/", response_model=List[ProductResponse], status_code=status.HTTP_200_OK)
async def read_fav_products(
    user_id: int = Query(gt=0, description="ID пользователя"),
    session: AsyncSession = Depends(get_db)
):
    return await FavoriteService.read_user_favorites(user_id=user_id, session=session)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fav_product(
    product_id: int,
    user_id: int = Query(gt=0, description="ID пользователя"),
    session: AsyncSession = Depends(get_db)
):
    await FavoriteService.delete_user_favorites(user_id=user_id, product_id=product_id, session=session)
    return