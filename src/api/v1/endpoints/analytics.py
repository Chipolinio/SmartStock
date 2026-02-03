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
    return await AnalyticsService.run_full_analytics(user_id=user_data["user_id"], days=days, session=session)