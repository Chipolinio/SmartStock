import httpx
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from bot.keyboards.main_menu import get_menu_kb

router = Router()

# Для бота используем базовый URL без /api/v1
API_BASE_URL = "http://127.0.0.1:8000"


@router.message(Command("start"))
async def cmd_start(message: types.Message, command: CommandObject = None):
    """Обработчик команды /start."""
    tg_id = message.from_user.id
    
    # Проверяем, есть ли аргумент (для /link через кнопку)
    if command and command.args:
        await process_link_command(message, command.args.strip(), tg_id)
        return

    text = (
        "👋 **Добро пожаловать в SmartStock!**\n\n"
        "**Команды:**\n"
        "/link <user_id> — привязать аккаунт (user_id из профиля на сайте)\n"
        "/analytics — аналитика по избранным\n"
        "/forecast — прогнозы\n"
        "/favorites — список избранного\n"
        "/unlink — отвязать Telegram\n\n"
        "**Как привязать аккаунт?**\n"
        "1. Зайди в профиль на сайте\n"
        "2. Скопируй 'My User ID'\n"
        "3. Отправь мне: `/link <user_id>`"
    )

    await message.answer(text, reply_markup=get_menu_kb(), parse_mode="Markdown")


@router.message(Command("link"))
async def cmd_link(message: types.Message, command: CommandObject):
    """Привязать аккаунт по user_id."""
    if not command.args:
        await message.answer(
            "❌ Ошибка: не указан user_id.\n\n"
            "Используй: `/link <user_id>` (user_id из профиля на сайте)"
        )
        return
    
    await process_link_command(message, command.args.strip(), message.from_user.id)


async def process_link_command(message: types.Message, user_id_str: str, tg_id: int):
    """Обработать команду привязки."""
    try:
        link_user_id = int(user_id_str)
    except ValueError:
        return await message.answer("❌ user_id должен быть числом!")

    async with httpx.AsyncClient() as client:
        try:
            # Оба параметра в query params
            response = await client.post(
                f"{API_BASE_URL}/user/telegram/link",
                params={"telegram_id": tg_id, "user_id": link_user_id}
            )

            if response.status_code == 200:
                data = response.json()
                await message.answer(
                    f"✅ **{data.get('message', 'Telegram привязан')}**\n\n"
                    "Теперь доступны команды:\n"
                    "/analytics — аналитика\n"
                    "/forecast — прогнозы\n"
                    "/favorites — избранное",
                    parse_mode="Markdown"
                )
            else:
                error_data = response.json()
                await message.answer(f"❌ Ошибка: {error_data.get('detail', 'Неизвестная ошибка')}")
                
        except httpx.RequestError as e:
            await message.answer(f"❌ Ошибка соединения: {e}")


@router.message(Command("unlink"))
async def cmd_unlink(message: types.Message):
    """Отвязать Telegram."""
    await message.answer(
        "Для отвязки Telegram зайди в профиль на сайте и нажми 'Отвязать Telegram'."
    )


@router.message(F.text == "👤 Профиль")
async def handle_profile(message: types.Message):
    """Кнопка Профиль."""
    await message.answer(
        f"👤 Профиль\n\n"
        f"Telegram ID: `{message.from_user.id}`\n\n"
        "Для привязки к аккаунту используй команду /link"
    )


@router.message(F.text == "❓ Помощь")
async def handle_help(message: types.Message):
    """Кнопка Помощь."""
    text = (
        "❓ Помощь\n\n"
        "Команды:\n"
        "/start — начать работу\n"
        "/link <user_id> — привязать аккаунт\n"
        "/analytics — аналитика\n"
        "/forecast — прогнозы\n"
        "/favorites — избранное\n"
        "/unlink — отвязать Telegram\n\n"
        "Кнопки:\n"
        "📊 Аналитика, 📈 Прогнозы, ⭐️ Избранное, 👤 Профиль"
    )
    await message.answer(text)
