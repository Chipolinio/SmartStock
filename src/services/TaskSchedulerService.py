from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date
from src.db.database import AsyncSessionLocal

from src.services.MLService import run_daily_forecast, run_model_training
from src.services.IntegrationService import WBScraper
from src.services import ProductService as ProductServiceModule, SalesService as SalesServiceModule
from src.services.DatabaseService import fill_daily_dataset


class TaskSchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def run_daily_pipeline(self):
        print("🚀 Старт ежедневного конвейера данных...")
        async with AsyncSessionLocal() as session:
            try:
                products = await ProductServiceModule.get_products_filter(session, limit=2500)
                articles = [p.product_id for p in products]
                if not articles:
                    print("⚠️ Нет товаров для работы")
                    return

                scraper = WBScraper()
                data_pack = await scraper.fetch_data(articles)

                await SalesServiceModule.process_full(data_pack, session)
                await session.flush()
                await fill_daily_dataset(session)
                await session.flush()

                await run_daily_forecast(session, date.today())

                await session.commit()
                print("✅ Пайплайн завершен успешно")
            except Exception as e:
                print(f"❌ Критический сбой пайплайна: {e}")
                await session.rollback()

    async def run_weekly_training(self):
        print("🧠 Старт обучения модели...")
        async with AsyncSessionLocal() as session:
            try:
                success = await run_model_training(session)
                if success:
                    await session.commit()
                    print("✅ Модель переобучена")
            except Exception as e:
                print(f"❌ Ошибка при обучении: {e}")

    def start(self):
        self.scheduler.add_job(self.run_daily_pipeline, "cron", hour=1, minute=0)
        self.scheduler.add_job(self.run_weekly_training, "cron", day_of_week="sun", hour=3, minute=0)

        self.scheduler.start()
        print("📅 Планировщик задач запущен")