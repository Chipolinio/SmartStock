from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐️ Избранное"), KeyboardButton(text="📊 Аналитика")],
            [KeyboardButton(text="👤 Мой профиль")]
        ],
        resize_keyboard=True
    )