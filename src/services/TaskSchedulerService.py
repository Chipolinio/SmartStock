from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date
from sqlalchemy import text
from src.db.database import AsyncSessionLocal

from src.services.MLService import run_daily_forecast, run_model_training
from src.services.IntegrationService import WBScraper
from src.services import ProductService as ProductServiceModule, SalesService as SalesServiceModule
from src.services.DatabaseService import fill_daily_dataset


class TaskSchedulerService:
    DAILY_PIPELINE_LOCK_KEY = 71001
    WEEKLY_TRAINING_LOCK_KEY = 71002

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def _acquire_lock(self, session, lock_key: int) -> bool:
        result = await session.execute(
            text("SELECT pg_try_advisory_lock(:lock_key)"),
            {"lock_key": lock_key},
        )
        return bool(result.scalar())

    async def _release_lock(self, session, lock_key: int) -> None:
        await session.execute(
            text("SELECT pg_advisory_unlock(:lock_key)"),
            {"lock_key": lock_key},
        )

    async def run_daily_pipeline(self):
        print("🚀 Старт ежедневного конвейера данных...")
        async with AsyncSessionLocal() as session:
            lock_acquired = False
            try:
                lock_acquired = await self._acquire_lock(session, self.DAILY_PIPELINE_LOCK_KEY)
                if not lock_acquired:
                    print("⏭️ Daily pipeline уже выполняется в другом процессе, запуск пропущен")
                    return

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
            finally:
                if lock_acquired:
                    await self._release_lock(session, self.DAILY_PIPELINE_LOCK_KEY)

    async def run_weekly_training(self):
        print("🧠 Старт обучения модели...")
        async with AsyncSessionLocal() as session:
            lock_acquired = False
            try:
                lock_acquired = await self._acquire_lock(session, self.WEEKLY_TRAINING_LOCK_KEY)
                if not lock_acquired:
                    print("⏭️ Weekly training уже выполняется в другом процессе, запуск пропущен")
                    return

                success = await run_model_training(session)
                if success:
                    await session.commit()
                    print("✅ Модель переобучена")
            except Exception as e:
                print(f"❌ Ошибка при обучении: {e}")
                await session.rollback()
            finally:
                if lock_acquired:
                    await self._release_lock(session, self.WEEKLY_TRAINING_LOCK_KEY)

    def start(self):
        self.scheduler.add_job(
            self.run_daily_pipeline,
            "cron",
            hour=1,
            minute=0,
            id="daily_pipeline",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.add_job(
            self.run_weekly_training,
            "cron",
            day_of_week="sun",
            hour=3,
            minute=0,
            id="weekly_training",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

        self.scheduler.start()
        print("📅 Планировщик задач запущен")