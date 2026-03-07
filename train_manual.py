import asyncio
import os
from src.db.database import AsyncSessionLocal
from src.services.MLService import run_model_training, run_daily_forecast


async def manual_train_and_check():
    print("🛠 Запуск ручного обучения модели...")

    async with AsyncSessionLocal() as session:
        success = await run_model_training(session)

        if success:
            print(f"✅ Модель обучена. Файл: {os.path.getsize('catboost_sales_model.bin') / 1024:.2f} KB")

            target_date = date(2026, 3, 1)
            print(f"\n🔮 Запуск прогноза через сервис за {target_date}...")

            res = await run_daily_forecast(session, target_date)

            if res:
                print(f"🚀 ПОБЕДА! Сервис обработал {len(res)} товаров и записал их в БД.")
            else:
                print(f"⚠️ Сервис вернул None. Проверь, что в product_features_daily есть данные за {target_date}")
        else:
            print("❌ Ошибка: run_model_training не смог собрать данные для обучения.")


if __name__ == "__main__":
    from datetime import date

    asyncio.run(manual_train_and_check())