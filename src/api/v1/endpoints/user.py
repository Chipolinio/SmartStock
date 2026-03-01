from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.db.database import get_db
from src.db.schemas.UserFavorite import (
    UserFavoriteCreateRequest,
    UserFavoriteResponse,
    UserFavoriteBatchRequest
)
from src.db.schemas.Product import ProductResponse
from src.services import UserService
from src.utils.dependencies import get_user

router = APIRouter()

@router.get("/favorites", response_model=List[ProductResponse])
async def read_fav_products(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    return await UserService.read_user_favorites(
        internal_id=user_data["user_id"],
        session=session
    )

@router.post("/favorites", response_model=UserFavoriteResponse, status_code=status.HTTP_201_CREATED)
async def create_favorite_product(
    fav_req: UserFavoriteCreateRequest,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    return await UserService.create_user_favorites(
        internal_id=user_data["user_id"],
        product_id=fav_req.product_id,
        session=session
    )

@router.post("/favorites/batch", status_code=status.HTTP_201_CREATED)
async def create_batch_favorites(
    batch_req: UserFavoriteBatchRequest,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    return await UserService.create_batch_favorites(
        internal_id=user_data["user_id"],
        product_ids=batch_req.product_ids,
        session=session
    )

@router.delete("/favorites/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fav_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    await UserService.delete_user_favorites(
        internal_id=user_data["user_id"],
        product_id=product_id,
        session=session
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)