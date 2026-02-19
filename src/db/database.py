import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# ВРЕМЕННО добавим принудительный вывод в консоль
print(f"DEBUG: Current DATABASE_URL is: {DATABASE_URL}")

if not DATABASE_URL or not DATABASE_URL.startswith("postgresql+asyncpg"):
    print("DEBUG: URL is wrong or not found, fixing it manually...")
    DATABASE_URL = "postgresql+asyncpg://admin:password@127.0.0.1:5434/smartstock"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()