from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_menu_kb():
    """Основное меню бота."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Аналитика"), KeyboardButton(text="📈 Прогнозы")],
            [KeyboardButton(text="⭐️ Избранное"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )