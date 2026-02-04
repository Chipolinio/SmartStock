import pandas as pd
import math
import numpy as np
import logging
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from src.db.repositories.AnalyticsRepository import get_analytics_dataset, get_price_changes

logger = logging.getLogger(__name__)


def apply_abc_xyz_classification(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df['abc'] = np.where(df['cum_share_pct'] <= 0.8, 'A',
                         np.where(df['cum_share_pct'] <= 0.95, 'B', 'C'))

    df['cv'] = df['sales_std'] / df['sales_avg'].replace(0, np.nan)
    df['xyz'] = np.where(df['cv'] <= 0.1, 'X',
                         np.where(df['cv'] <= 0.25, 'Y', 'Z'))

    df['abc'] = df['abc'].fillna('C')
    df['xyz'] = df['xyz'].fillna('Z')
    df['cv'] = df['cv'].fillna(0)

    return df


def get_product_scoring(row: pd.Series) -> float:
    try:
        rating_norm = float(row.get('avg_rating') or 0) / 5
        reviews_norm = np.log1p(float(row.get('max_feedbacks') or 0)) / 10
        delivery_norm = 1 / (float(row.get('avg_delivery') or 5) + 1)

        score = (rating_norm * 0.4) + (reviews_norm * 0.3) + (delivery_norm * 0.3)

        if not math.isfinite(score):
            return 0.0

        return round(float(np.clip(score, 0, 1)), 2)
    except:
        return 0.0


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
        df = df.replace({np.nan: 0, np.inf: 0, -np.inf: 0})
        final_results = []
        for _, row in df.iterrows():
            score = get_product_scoring(row)

            if not np.isfinite(score):
                score = 0.0

            final_results.append({
                "product_id": int(row['product_id']),
                "subject": str(row['subject']) if row['subject'] else "Неизвестно",
                "metrics": {
                    "abc": str(row['abc']),
                    "xyz": str(row['xyz']),
                    "segment": f"{row['abc']}{row['xyz']}",
                    "score": float(score),  # Явное приведение
                    "revenue": round(float(row.get('total_revenue') or 0), 2)
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


async def check_price_alerts(user_id: int, session: AsyncSession, threshold: float = 5.0):
    raw_changes = await get_price_changes(session=session, user_id=user_id)

    alerts = []
    for row in raw_changes:
        try:
            # Преобразуем в float и проверяем на None/0
            prev = float(row.previous_price or 0)
            curr = float(row.current_price or 0)

            # ЗАЩИТА: Если предыдущая цена 0, мы не можем посчитать % изменения
            if prev <= 0:
                continue

            diff_pct = ((prev - curr) / prev) * 100

            if diff_pct >= threshold and curr > 0:
                alerts.append({
                    "product_id": row.product_id,
                    "name": row.name,
                    "old_price": prev,
                    "new_price": curr,
                    "diff_pct": round(diff_pct, 1),
                    "date": row.dt
                })
        except (ZeroDivisionError, TypeError, ValueError) as e:
            logger.warning(f"Ошибка расчета алерта для товара {row.product_id}: {e}")
            continue

    return alerts