import numpy as np
import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.AnalyticsRepository import fetch_universal_data
from src.db.schemas.Analytics import (
    AnalyticsRequest,
    AnalyticsEntry,
    AnalyticsMetrics,
)

logger = logging.getLogger(__name__)


def get_recommendation_text(abc: str, xyz: str, score: float) -> str:
    segment = f"{abc}{xyz}"
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


async def run_unified_analytics(session: AsyncSession, user_id: int, q: AnalyticsRequest) -> List[AnalyticsEntry]:
    try:
        raw_rows = await fetch_universal_data(session, user_id, q)

        final_results = []
        for row in raw_rows:
            std_dev = row.get('sales_std') or 0
            avg_sales = row.get('sales_avg') or 0

            cv = (float(std_dev) / float(avg_sales)) if float(avg_sales) > 0 else 0

            r_norm = float(row.get('avg_rating') or 0) / 5
            f_norm = np.log1p(float(row.get('max_feedbacks') or 0)) / 10
            d_norm = 1 / (float(row.get('avg_delivery') or 5) + 1)
            calculated_score = round(float(np.clip((r_norm * 0.4) + (f_norm * 0.3) + (d_norm * 0.3), 0, 1)), 2)

            abc_val = row.get('abc_sql') or 'C'
            xyz_val = 'X' if cv <= 0.1 else ('Y' if cv <= 0.25 else 'Z')

            m = AnalyticsMetrics()
            if "revenue" in q.metrics: m.revenue = round(float(row.get('total_revenue') or 0), 2)
            if "sales" in q.metrics: m.sales = int(row.get('total_sales') or 0)
            if "abc" in q.metrics: m.abc = abc_val
            if "xyz" in q.metrics: m.xyz = xyz_val
            if "score" in q.metrics: m.score = calculated_score
            if "rating" in q.metrics: m.avg_rating = round(row.get('avg_rating') or 0, 1)

            entry = AnalyticsEntry(
                dimensions={d: row.get(d) for d in q.dimensions},
                metrics=m,
                recommendation=get_recommendation_text(abc_val, xyz_val, calculated_score)
                if "recommendation" in q.metrics else None
            )
            final_results.append(entry)

        return final_results

    except Exception as e:
        logger.error(f"Analytics Pipeline Error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during analytics processing"
        )