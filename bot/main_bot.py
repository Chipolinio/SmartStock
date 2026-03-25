import asyncio
from aiogram import Bot, Dispatcher
from settings import settings
from src.db.database import AsyncSessionLocal
from bot.middlewares.db_session import DbSessionMiddleware
from bot.middlewares.auth import AuthMiddleware
from bot.handlers.start import router as start_router
from bot.handlers.menu import router as menu_router
from bot.handlers.analytics import router as analytics_router

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    dp.update.middleware(DbSessionMiddleware(AsyncSessionLocal))

    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(analytics_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())