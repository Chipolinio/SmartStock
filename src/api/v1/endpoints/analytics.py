from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.services import AnalyticsService as AnalyticsServiceModule
from src.db.schemas.Analytics import AnalyticsResponse, AnalyticsRequest
from src.utils.dependencies import get_user, is_user_pro

router = APIRouter()


@router.post(
    "/aggregate",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    description="""
    Универсальный эндпоинт для аналитики.
    
    **Примеры использования:**
    1. **Динамика:** dimensions=['dt'], metrics": ["revenue", "sales"]
    2. **Категории:** dimensions=['subject'], metrics=['revenue', 'abc']
    3. **Товары:** dimensions=['product_id'], metrics=['abc', 'xyz', 'recommendation']
    4. **Бренды:** dimensions: ["brand"],metrics: ["revenue", "sales", "rating"]
    5. **Матрица:** "dimensions": ["product_id"],"metrics": ["revenue", "sales", "abc", "xyz", "score", "recommendation", "rating"],"filters": {"subject": ["кофемашины"]}
    """
)
async def get_aggregated_analytics(
    query: AnalyticsRequest,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    data = await AnalyticsServiceModule.run_unified_analytics(
        session=session,
        user_id=user_data["user_id"],
        q=query
    )
    return {"status": "success", "data": data}