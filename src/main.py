from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.db.database import AsyncSessionLocal

from src.services.IntegrationService import WBScraper
from src.services import ProductService
from src.services import SalesService
from src.services.DatabaseService import fill_daily_dataset
from src.utils.logger import setup_logging

setup_logging()
app = FastAPI()


async def run_daily_pipeline():
    print("🚀 Старт ежедневного конвейера данных...")
    async with AsyncSessionLocal() as session:
        try:
            products = await ProductService.get_products_filter(session, limit=2500)
            articles = [p.product_id for p in products]

            if not articles:
                print("⚠️ Список продуктов пуст, скрапинг отменен")
                return

            scraper = WBScraper()
            data_pack = await scraper.fetch_data(articles)

            await SalesService.process_full(data_pack, session)
            await session.flush()
            await fill_daily_dataset(session)
            await session.commit()

            print("✅ Все этапы конвейера завершены успешно")
        except Exception as e:
            print(f"❌ Критический сбой пайплайна: {e}")
            await session.rollback()


@app.on_event("startup")
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_daily_pipeline, "cron", hour=1, minute=0)
    scheduler.start()