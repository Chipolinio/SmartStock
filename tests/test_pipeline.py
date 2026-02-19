import asyncio
from src.main import run_daily_pipeline

async def test():
    print("🧪 Начинаем тестовый запуск пайплайна...")
    await run_daily_pipeline()
    print("🏁 Тест завершен.")

if __name__ == "__main__":
    asyncio.run(test())