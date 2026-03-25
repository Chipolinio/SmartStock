from aiogram import Router, F, types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.services.AnalyticsBotService import (
    get_favorites_analytics_summary,
    get_favorites_forecasts
)
from src.db.models.User import User
from src.db.repositories.UserFavoriteRepositories import read_user_favorites

router = Router()


@router.message(F.text == "📊 Аналитика")
async def handle_analytics(message: types.Message, session: AsyncSession):
    """Обработчик кнопки 'Аналитика'."""
    tg_id = message.from_user.id
    
    # Проверяем привязку
    user_stmt = select(User).where(User.user_id == tg_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return await message.answer(
            "❌ Telegram не привязан к аккаунту.\n\n"
            "Используй команду /link <код> для привязки."
        )
    
    await message.answer("⏳ Анализирую ваши продажи за 30 дней...")

    analytics_data = await get_favorites_analytics_summary(user.id, session)

    if analytics_data["total_products"] == 0:
        return await message.answer("Список избранного пуст или данных недостаточно.")

    response = "📊 *ABC-Анализ избранных товаров:*\n\n"
    response += f"• Всего товаров: {analytics_data['total_products']}\n"
    response += f"• Класс A (лидеры): {analytics_data['class_a_count']}\n"
    response += f"• Класс B (середнячки): {analytics_data['class_b_count']}\n"
    response += f"• Класс C (аутсайдеры): {analytics_data['class_c_count']}\n"
    response += f"• Общая выручка: {analytics_data['total_revenue']:,.0f} ₽\n\n"
    
    if analytics_data["abc_data"]:
        response += "*Топ-5 товаров:*\n"
        for item in analytics_data["abc_data"]:
            emoji = "🟢" if item.abc_class == "A" else ("🟡" if item.abc_class == "B" else "🔴")
            name = item.product_name[:30] + "..." if len(item.product_name) > 30 else item.product_name
            # Экранируем спецсимволы Markdown
            name_escaped = name.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            response += f"{emoji} {name_escaped} — {item.total_revenue:,.0f} ₽\n"
    
    await message.answer(response, parse_mode="Markdown")


@router.message(F.text == "📈 Прогнозы")
async def handle_forecasts(message: types.Message, session: AsyncSession):
    """Обработчик кнопки 'Прогнозы'."""
    tg_id = message.from_user.id
    
    # Проверяем привязку
    user_stmt = select(User).where(User.user_id == tg_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return await message.answer(
            "❌ Telegram не привязан к аккаунту.\n\n"
            "Используй команду /link <код> для привязки."
        )
    
    await message.answer("⏳ Рассчитываю прогноз по остаткам...")

    forecast_list = await get_favorites_forecasts(user.id, session)

    if not forecast_list:
        return await message.answer("Нет активных прогнозов для ваших товаров.")

    response = "📈 *Прогноз продаж (ML):*\n\n"
    for f in forecast_list:
        name = f['product_name'][:30] + "..." if len(f['product_name']) > 30 else f['product_name']
        # Экранируем спецсимволы Markdown в пользовательских данных
        name_escaped = name.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
        model_escaped = f['model_version'].replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
        response += f"📦 *Товар {f['product_id']}*\n"
        response += f"└ {name_escaped}\n"
        response += f"└ Прогноз: ~{f['predicted_sales']:.1f} шт/день\n"
        response += f"└ Модель: {model_escaped}\n\n"

    await message.answer(response, parse_mode="Markdown")


@router.message(F.text == "👤 Мой профиль")
async def handle_profile(message: types.Message, session: AsyncSession):
    """Обработчик кнопки 'Профиль'."""
    tg_id = message.from_user.id
    
    user_stmt = select(User).where(User.user_id == tg_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        return await message.answer(
            "❌ Профиль не найден.\n\n"
            "Используй команду /link <код> для привязки."
        )

    text = (
        f"👤 **Профиль {user.email}**\n\n"
        f"💎 Статус: `{'PRO' if user.is_pro else 'Basic'}`\n"
        f"⚙️ Активен: `{'Да' if user.is_active else 'Нет'}`\n"
        f"🔑 Telegram ID: `{tg_id}`"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "⭐️ Избранное")
async def favorites(message: types.Message, session: AsyncSession):
    """Обработчик кнопки 'Избранное'."""
    tg_id = message.from_user.id
    
    # Проверяем привязку
    user_stmt = select(User).where(User.user_id == tg_id)
    user_result = await session.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    
    if not user:
        return await message.answer(
            "❌ Telegram не привязан к аккаунту.\n\n"
            "Используй команду /link <код> для привязки."
        )

    try:
        favs = await read_user_favorites(user.id, session)

        if not favs:
            await message.answer("Твой список избранного пуст. Добавь что-нибудь на сайте!")
            return

        response_text = "⭐️ *Твое избранное:*\n\n"
        for i, p in enumerate(favs[:10], 1):
            name = p.name[:30] + "..." if len(p.name) > 30 else p.name
            # Экранируем спецсимволы Markdown
            name_escaped = name.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
            response_text += f"{i}. {name_escaped} (арт. {p.product_id})\n"

        if len(favs) > 10:
            response_text += f"\n... и ещё {len(favs) - 10} товаров"

        await message.answer(response_text, parse_mode="Markdown")

    except Exception as e:
        print(f"BOT ERROR: {e}")
        await message.answer("Произошла ошибка при получении списка. Убедись, что Telegram привязан в личном кабинете.")


@router.message(F.text == "❓ Помощь")
async def handle_help(message: types.Message):
    """Обработчик кнопки 'Помощь'."""
    text = (
        "❓ **Помощь по боту SmartStock**\n\n"
        "**Команды:**\n"
        "/start — начать работу с ботом\n"
        "/link <код> — привязать аккаунт по коду с сайта\n"
        "/analytics — показать ABC-анализ избранных товаров\n"
        "/forecast — показать прогнозы продаж\n"
        "/favorites — список избранных товаров\n"
        "/unlink — отвязать Telegram\n\n"
        "**Кнопки меню:**\n"
        "📊 Аналитика — ABC-анализ твоих товаров\n"
        "📈 Прогнозы — прогнозы продаж на основе ML\n"
        "⭐️ Избранное — список твоих избранных товаров\n"
        "👤 Профиль — информация об аккаунте\n\n"
        "**Как привязать аккаунт?**\n"
        "1. Зайди в личный кабинет на сайте\n"
        "2. Нажми 'Привязать Telegram'\n"
        "3. Скопируй код и отправь боту: `/link <код>`"
    )
    await message.answer(text, parse_mode="Markdown")