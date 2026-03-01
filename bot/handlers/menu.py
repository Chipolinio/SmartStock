from aiogram import Router, F, types
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.AnalyticsBotService import (
    get_favorites_analytics_summary,
    get_favorites_forecasts
)
from src.db.repositories import UserRepositories as UserRepo
from src.db.repositories import UserFavoriteRepositories as FavRepo

router = Router()


@router.message(F.text == "📊 Аналитика")
async def handle_analytics(message: types.Message, session: AsyncSession):
    tg_id = message.from_user.id
    await message.answer("⏳ Анализирую ваши продажи за 30 дней...")

    analytics_data = await get_favorites_analytics_summary(tg_id, session)

    if not analytics_data:
        return await message.answer("Список избранного пуст или данных недостаточно.")

    response = "📊 **ABC/XYZ Анализ:**\n\n"
    for entry in analytics_data:
        m = entry.metrics
        response += (
            f"📦 **Арт: {entry.dimensions['product_id']}**\n"
            f"└ Сегмент: `{m.abc}{m.xyz}` | Скоринг: `{m.score}`\n"
            f"💡 _{entry.recommendation}_\n\n"
        )
    await message.answer(response, parse_mode="Markdown")


@router.message(F.text == "📈 Прогнозы")
async def handle_forecasts(message: types.Message, session: AsyncSession):
    tg_id = message.from_user.id
    await message.answer("⏳ Рассчитываю прогноз по остаткам...")

    forecast_list = await get_favorites_forecasts(tg_id, session)

    if not forecast_list:
        return await message.answer("Нет активных прогнозов для ваших товаров.")

    response = "📈 **Прогноз остатков (ML):**\n\n"
    for f in forecast_list:
        p = f["prediction"]
        status_icon = "🚨" if f["alerts"]["critical_oos"] else "⚠️" if f["alerts"]["is_low_stock"] else "✅"

        response += (
            f"{status_icon} **Товар {f['product_id']}**\n"
            f"└ Склад: `{f['current_stock']} шт.`\n"
            f"└ Прогноз: `~{p['sales_next_day']} шт./день`\n"
            f"└ **Хватит на: {p['days_until_out_of_stock']} дн.**\n\n"
        )
    await message.answer(response, parse_mode="Markdown")


@router.message(F.text == "👤 Мой профиль")
async def handle_profile(message: types.Message, session: AsyncSession):
    user = await UserRepo.read_user_by_id(message.from_user.id, session)

    if not user:
        return await message.answer("Профиль не найден. Привяжите ID на сайте.")

    text = (
        f"👤 **Профиль {user.email}**\n\n"
        f"💎 Статус: `{'PRO' if user.is_pro else 'Basic'}`\n"
        f"⚙️ Активен: `{'Да' if user.is_active else 'Нет'}`\n"
        f"🔑 ID для привязки: `{message.from_user.id}`"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "⭐️ Избранное")
async def favorites(message: types.Message, session: AsyncSession):
    tg_id = message.from_user.id

    try:
        favs = await FavRepo.read_user_favorites(user_id=tg_id, session=session)

        if not favs:
            await message.answer("Твой список избранного пуст. Добавь что-нибудь на сайте!")
            return

        response_text = "⭐️ **Твое избранное:**\n\n"
        for p in favs:
            response_text += f"🔹 {p.name} (арт. {p.product_id})\n"

        await message.answer(response_text, parse_mode="Markdown")

    except Exception as e:
        print(f"BOT ERROR: {e}")
        await message.answer("Произошла ошибка при получении списка. Убедись, что Telegram привязан в личном кабинете.")