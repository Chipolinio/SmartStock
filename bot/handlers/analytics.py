"""
Обработчики команд для аналитики и прогнозов.
"""
from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.db.models.User import User
from src.db.repositories.UserFavoriteRepositories import read_user_favorites
from src.db.repositories.AnalyticsRepository import (
    get_abc_data,
    get_top_products_by_revenue
)
from src.db.repositories.PredictedSalesTSRepositories import read_latest_prediction
from src.db.models.PriceTS import PriceTS
from sqlalchemy import select

router = Router()


@router.message(Command("analytics"))
async def cmd_analytics(message: types.Message, session: AsyncSession):
    """Показать аналитику по избранным товарам."""
    tg_id = message.from_user.id
    
    # Проверяем, привязан ли Telegram
    user_stmt = select(User).where(User.user_id == tg_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        await message.answer(
            "❌ Telegram не привязан к аккаунту.\n\n"
            "Используй команду /link <код> для привязки."
        )
        return

    # Получаем ABC-анализ
    try:
        abc_data = await get_abc_data(user.id, session, days=30)
        
        if not abc_data.data:
            await message.answer("📭 У тебя пока нет избранных товаров с аналитикой.")
            return
        
        # Группируем по классам
        by_class = {"A": [], "B": [], "C": []}
        for item in abc_data.data:
            by_class[item.abc_class].append(item)
        
        text = "📊 **ABC-анализ избранных товаров:**\n\n"
        
        for cls in ["A", "B", "C"]:
            items = by_class[cls][:3]  # Показываем топ-3 в каждой категории
            if items:
                emoji = "🟢" if cls == "A" else ("🟡" if cls == "B" else "🔴")
                text += f"{emoji} **Класс {cls}** ({len(by_class[cls])} товаров):\n"
                for item in items:
                    text += f"  • {item.product_name[:40]} — {item.total_revenue:,.0f} ₽\n"
        
        await message.answer(text, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка получения аналитики: {e}")


@router.message(Command("forecast"))
async def cmd_forecast(message: types.Message, session: AsyncSession):
    """Показать прогнозы по избранным товарам."""
    tg_id = message.from_user.id
    
    # Проверяем, привязан ли Telegram
    user_stmt = select(User).where(User.user_id == tg_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        await message.answer(
            "❌ Telegram не привязан к аккаунту.\n\n"
            "Используй команду /link <код> для привязки."
        )
        return
    
    # Получаем избранные товары
    favorites = await read_user_favorites(user.id, session)
    
    if not favorites:
        await message.answer("📭 У тебя пока нет избранных товаров.")
        return
    
    # Получаем прогнозы
    total_predicted = 0
    oos_risk_count = 0
    forecasts_text = ""
    
    for product in favorites[:5]:  # Показываем первые 5
        prediction = await read_latest_prediction(product.product_id, session)
        if prediction:
            total_predicted += float(prediction.predicted_sales)
            
            # Получаем текущие остатки
            stock_stmt = select(PriceTS.price_sale).where(
                PriceTS.product_id == product.product_id
            ).order_by(PriceTS.dt.desc()).limit(1)
            
            forecasts_text += f"• {product.name[:40]}: {prediction.predicted_sales:.1f} шт/день\n"
    
    avg_predicted = total_predicted / len(favorites) if favorites else 0
    
    text = "🔮 **Прогнозы по избранным товарам:**\n\n"
    text += f"• Товаров в избранном: {len(favorites)}\n"
    text += f"• Средний прогноз: {avg_predicted:.1f} шт/день\n\n"
    
    if forecasts_text:
        text += "**По товарам:**\n" + forecasts_text
    
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("favorites"))
async def cmd_favorites(message: types.Message, session: AsyncSession):
    """Показать список избранных товаров."""
    tg_id = message.from_user.id
    
    # Проверяем, привязан ли Telegram
    user_stmt = select(User).where(User.user_id == tg_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        await message.answer(
            "❌ Telegram не привязан к аккаунту.\n\n"
            "Используй команду /link <код> для привязки."
        )
        return
    
    # Получаем избранные товары
    favorites = await read_user_favorites(user.id, session)
    
    if not favorites:
        await message.answer(
            "📭 У тебя пока нет избранных товаров.\n\n"
            "Добавляй товары на сайте, и они появятся здесь!"
        )
        return
    
    text = "❤️ **Твои избранные товары:**\n\n"
    for i, product in enumerate(favorites[:10], 1):
        name = product.name[:50] if product.name else "Unknown"
        text += f"{i}. {name} (ID: {product.product_id})\n"
    
    if len(favorites) > 10:
        text += f"\n... и ещё {len(favorites) - 10} товаров (показаны первые 10)"
    
    await message.answer(text, parse_mode="Markdown")
