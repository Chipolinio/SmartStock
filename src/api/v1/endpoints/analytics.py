from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Annotated

from src.db.database import get_db
from src.services import AnalyticsService
from src.db.schemas.Analytics import ProductAnalyticsResponse
from src.utils.dependencies import get_user, is_user_pro

router = APIRouter()

@router.get("/",response_model=List[ProductAnalyticsResponse], status_code=status.HTTP_200_OK)
async def analytics(
        days: Annotated[int, Query(gt=0, le=365, description="Период аналитики в днях")] = 30,
        user_data: dict = Depends(get_user),
        session: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.run_analytics(
        user_id=user_data["user_id"],
        days=days,
        session=session)

@router.get("/price-alerts", status_code=200)
async def get_product_price_alerts(
    user_data: dict = Depends(get_user),
    threshold: float = Query(5.0, gt=0, le=100, description="Порог падения цены в %"),
    session: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.check_price_alerts(
        user_id=user_data["user_id"],
        session=session,
        threshold=threshold
    )

@router.get("/matrix", status_code=status.HTTP_200_OK)
async def get_matrix_abc_xyz(
        user_data: dict = Depends(get_user),
        session: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_matrix_data(
        user_id=user_data["user_id"],
        session=session)

@router.get("/category", status_code=status.HTTP_200_OK)
async def get_category_share(
        user_data: dict = Depends(get_user),
        session: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_category_share(
        user_id=user_data["user_id"],
        session=session)

@router.get("/history/{product_id}", status_code=status.HTTP_200_OK)
async def get_product_history(
        product_id: int,
        user_data: dict = Depends(get_user),
        days: Annotated[int, Query(gt=0, le=365)] = 30,
        session: AsyncSession = Depends(get_db)
):
    return await AnalyticsService.get_product_history(
        product_id=product_id,
        user_id=user_data["user_id"],
        session=session,
        days=days
    )