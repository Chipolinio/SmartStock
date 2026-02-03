import pandas as pd
import numpy as np
import logging
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from src.db.repositories.AnalyticsRepository import get_analytics_dataset

logger = logging.getLogger(__name__)


def apply_abc_xyz_classification(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df['abc'] = np.where(df['cum_share_pct'] <= 0.8, 'A',
                         np.where(df['cum_share_pct'] <= 0.95, 'B', 'C'))

    df['cv'] = df['sales_std'] / df['sales_avg'].replace(0, np.nan)
    df['xyz'] = np.where(df['cv'] <= 0.1, 'X',
                         np.where(df['cv'] <= 0.25, 'Y', 'Z'))
    df['xyz'] = df['xyz'].fillna('Z')

    return df


def get_product_scoring(row: pd.Series) -> float:
    rating_norm = float(row.get('avg_rating') or 0) / 5
    reviews_norm = np.log1p(float(row.get('max_feedbacks') or 0)) / 10
    delivery_norm = 1 / (float(row.get('avg_delivery') or 5) + 1)

    score = (rating_norm * 0.4) + (reviews_norm * 0.3) + (delivery_norm * 0.3)
    return round(float(np.clip(score, 0, 1)), 2)


def get_recommendation_text(row: pd.Series, score: float) -> str:
    segment = f"{row['abc']}{row['xyz']}"

    rules = {
        "AX": "Хит: поддерживайте остатки и не снижайте цену.",
        "CZ": "Неликвид: рассмотрите вывод товара из ассортимента.",
        "AZ": "Рискованный товар: высокий оборот при нестабильном спросе.",
        "CX": "Стабильный аутсайдер: малые продажи, но предсказуемые."
    }

    advice = rules.get(segment, "Средние показатели: следите за динамикой.")
    if score < 0.45:
        advice += " Срочно: низкий скоринг, проверьте отзывы/логистику."

    return advice


async def run_full_analytics(user_id: int, session: AsyncSession, days: int = 30) -> List[Dict[str, Any]]:
    try:
        result = await get_analytics_dataset(session=session, user_id=user_id, days=days)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Данные за последние {days} дн. не найдены"
            )

        df = pd.DataFrame([row for row in result])

        df = apply_abc_xyz_classification(df)

        final_results = []
        for _, row in df.iterrows():
            score = get_product_scoring(row)

            revenue_val = float(row.get('total_revenue') or 0)

            final_results.append({
                "product_id": int(row['product_id']),
                "subject": row['subject'],
                "metrics": {
                    "abc": row['abc'],
                    "xyz": row['xyz'],
                    "segment": f"{row['abc']}{row['xyz']}",
                    "score": score,
                    "revenue": round(revenue_val, 2)
                },
                "advice": get_recommendation_text(row, score)
            })

        return final_results

    except SQLAlchemyError as e:
        logger.error(f"DB Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при запросе к базе данных"
        )
    except HTTPException as e:
        logger.error(f"Request Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Не найдено"
        )
    except Exception as e:
        logger.error(f"Analytics Pipeline Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервиса аналитики"
        )