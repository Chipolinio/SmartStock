from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from settings import settings
from src.db.database import get_db
from src.db.schemas.AdRecommendation import (
    AdRecommendationGenerateRequest,
    AdRecommendationResponse,
    AdRecommendationsListResponse,
)
from src.services import AdCampaignService as AdCampaignServiceModule
from src.utils.dependencies import get_user

router = APIRouter()


@router.get(
    "/",
    response_model=AdRecommendationsListResponse,
    summary="Рекомендации по рекламе",
)
async def get_ad_recommendations(
    limit: int = Query(default=50, ge=1, le=200),
    category: str | None = Query(None, description="Фильтр по категории"),
    product_id: int | None = Query(None, gt=0),
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user),
):
    """Получить рекомендации по рекламе для текущего пользователя."""
    result = await AdCampaignServiceModule.get_user_recommendations(
        session=session,
        user_id=user_data["user_id"],
        limit=limit,
        product_id=product_id,
        category=category,
    )
    return result


@router.post(
    "/generate",
    response_model=list[AdRecommendationResponse],
    summary="Сгенерировать рекомендации",
)
async def generate_ad_recommendations(
    body: AdRecommendationGenerateRequest,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user),
):
    """Сгенерировать рекомендации по рекламе через LLM."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Generate request: prompt_type={body.prompt_type}, product_ids={body.product_ids}")

    return await AdCampaignServiceModule.generate_ad_recommendations(
        session=session,
        user_id=user_data["user_id"],
        llm_api_key=settings.LLM_API_KEY,
        product_ids=body.product_ids,
        prompt_type=body.prompt_type,
    )
