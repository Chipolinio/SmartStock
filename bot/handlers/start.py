from aiogram import Router, types
from aiogram.filters import Command
from bot.keyboards.main_menu import get_menu_kb

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = message.from_user.id

    text = (
        "👋 **Добро пожаловать в SmartStock!**\n\n"
        f"Твой уникальный ID: `{tg_id}`\n\n"
        "**Как синхронизировать аккаунт?**\n"
        "1. Скопируй ID выше.\n"
        "2. Зайди в личный кабинет на сайте.\n"
        "3. Вставь его в поле привязки Telegram.\n\n"
        "После этого ты сможешь просматривать свои товары прямо здесь!"
    )

    await message.answer(text, reply_markup=get_menu_kb(), parse_mode="Markdown")