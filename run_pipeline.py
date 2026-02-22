import asyncio
from src.main import app, lifespan
from src.services.TaskSchedulerService import TaskSchedulerService


async def manual_test():
    print("🧪 Начинаем ручной запуск пайплайна...")
    async with lifespan(app):
        scheduler_service = TaskSchedulerService()
        print("🛠 Вызываем run_daily_pipeline напрямую...")
        await scheduler_service.run_daily_pipeline()

        # Если нужно проверить еще и обучение модели:
        # await scheduler_service.run_weekly_training()

    print("🏁 Ручной запуск завершен.")


if __name__ == "__main__":
    try:
        asyncio.run(manual_test())
    except KeyboardInterrupt:
        print("🛑 Остановлено пользователем")
    except Exception as e:
        print(f"💥 Ошибка исполнения: {e}")