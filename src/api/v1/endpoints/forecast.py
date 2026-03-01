from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db
from src.services import MLService
from src.db.schemas.Forecast import FullForecastResponse

router = APIRouter()

@router.get("/{product_id}/full-analysis", response_model=FullForecastResponse)
async def get_full_analysis(product_id: int, session: AsyncSession = Depends(get_db)):
    res = await MLService.get_full_analysis(session, product_id)
    if not res:
        raise HTTPException(status_code=404, detail="Analysis data not found")
    return res

@router.get("/{product_id}/history")
async def get_history(product_id: int, limit: int = 30, session: AsyncSession = Depends(get_db)):
    return await MLService.get_forecast_history(session, product_id, limit)