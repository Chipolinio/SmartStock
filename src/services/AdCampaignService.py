import json
import logging
from typing import Any

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.repositories.AdRecommendationRepositories import (
    count_recommendations_by_user,
    create_ad_recommendations_bulk,
    read_recommendations_by_user,
)
from src.db.repositories.ProductFeaturesDailyRepositories import (
    read_features_latest,
)
from src.db.repositories.UserFavoriteRepositories import (
    read_user_favorites_with_details,
)
from src.db.schemas.AdRecommendation import AdRecommendationCreate

logger = logging.getLogger(__name__)

LLM_URL = "https://api.x.ai/v1/responses"
LLM_MODEL = "grok-3"


def _build_prompt(products_data: list[dict[str, Any]], prompt_type: str) -> str:
    products_str = "\n".join(
        f"- {p['name']} (арт.{p['product_id']}): {p['price']}₽, {p.get('avg_sales', '?')} прод/д, "
        f"остаток {p.get('stock_left', '?')} шт, рейтинг {p.get('rating', '?')}, "
        f"отзывов {p.get('feedbacks', '?')}"
        for p in products_data
    )

    base = f"Товары:\n{products_str}\n\n"

    tasks = {
        "full": "Полный аудит: 1) что продвигать и почему 2) бюджет 3) 3-5 ключевых фраз на товар 4) стратегия 5) риски. Не продвигай товары с остатком <3 дневных продаж или рейтингом <4.0.",
        "campaign": "Какие товары продвигать, тип кампании (поиск/товарная/ретаргетинг), ожидаемый эффект. Не продвигай товары с остатком <3 дневных продаж или рейтингом <4.0.",
        "keywords": "3-5 конкретных ключевых фраз на товар, пометь: горячая/тёплая. Избегай широких фраз.",
        "budget": "Дневной/месячный бюджет, распределение по товарам в ₽/%, обоснование, ожидаемый ROI.",
    }

    task = tasks.get(prompt_type, tasks["full"])

    return (
        f"Ты — маркетолог для продавцов на маркетплейсах. Давай конкретные рекомендации с цифрами.\n\n"
        f"{base}Задача: {task}"
    )


def _extract_llm_text(data: dict[str, Any]) -> str:
    """Извлечь текст из ответа xAI Responses API."""
    for item in data.get("output") or []:
        if item.get("type") != "message":
            continue
        for part in item.get("content") or []:
            if part.get("type") == "output_text" and part.get("text"):
                return part["text"]
    raise KeyError("no output_text in LLM response")


async def _call_llm(prompt: str, api_key: str) -> str:
    payload = {
        "model": LLM_MODEL,
        "input": [{"role": "user", "content": prompt}],
        "max_output_tokens": 1000,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            LLM_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    if resp.status_code != 200:
        logger.error("LLM API error: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Ошибка LLM API")

    data = resp.json()
    try:
        return _extract_llm_text(data)
    except KeyError as e:
        logger.error("Unexpected LLM response structure: %s; body=%s", e, data)
        raise HTTPException(status_code=502, detail="Неверный формат ответа LLM")


async def _gather_products_data(
    session: AsyncSession,
    user_id: int,
    product_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    favorites = await read_user_favorites_with_details(user_id, session)
    if not favorites:
        return []

    if product_ids:
        favorites = [
            (product, price, stock)
            for product, price, stock in favorites
            if product.product_id in product_ids
        ]

    products_data = []
    for product, price, stock in favorites:
        features = await read_features_latest(product.product_id, session)

        products_data.append({
            "product_id": product.product_id,
            "name": product.name or f"Товар {product.product_id}",
            "price": float(price) if price else 0,
            "avg_sales": getattr(features, "avg_sales_7d", None),
            "stock_left": int(stock) if stock else 0,
            "rating": getattr(features, "rating", None),
            "feedbacks": getattr(features, "feedbacks", None),
        })

    return products_data


async def generate_ad_recommendations(
    session: AsyncSession,
    user_id: int,
    llm_api_key: str,
    product_ids: list[int] | None = None,
    prompt_type: str = "full",
):
    if not llm_api_key:
        raise HTTPException(status_code=503, detail="LLM_API_KEY не настроен")

    products_data = await _gather_products_data(session, user_id, product_ids)
    if not products_data:
        raise HTTPException(status_code=404, detail="Нет данных о товарах")

    prompt = _build_prompt(products_data, prompt_type)
    response_text = await _call_llm(prompt, llm_api_key)

    records = [
        AdRecommendationCreate(
            user_id=user_id,
            product_id=None,
            category=prompt_type,
            recommendation_text=response_text,
            priority=1,
            metadata_json=json.dumps({
                "prompt_type": prompt_type,
                "products_count": len(products_data),
            }),
        )
    ]

    saved = await create_ad_recommendations_bulk(records, session)
    await session.commit()
    return saved


async def get_user_recommendations(
    session: AsyncSession,
    user_id: int,
    limit: int = 50,
    product_id: int | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    items = await read_recommendations_by_user(
        user_id, session, limit=limit, product_id=product_id, category=category
    )
    total = await count_recommendations_by_user(user_id, session)
    return {"items": items, "total": total}
