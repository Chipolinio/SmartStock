"""
Главный conftest.py для всех тестов.

Содержит общие фикстуры:
- event_loop — асинхронный цикл
- engine — тестовый DB engine
- db_session — тестовая сессия БД
- client — тестовый HTTP клиент (httpx.AsyncClient)
- mocker — pytest-mock фикстура
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from settings import settings
from src.db.models import Base
from src.db.database import get_db
from src.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для асинхронных тестов."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def engine():
    """Создает тестовый database engine."""
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        poolclass=NullPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine):
    """Создает тестовую сессию БД."""
    session = AsyncSession(bind=engine, expire_on_commit=False)

    yield session
    await session.close()


@pytest.fixture(scope="function")
async def client(db_session):
    """
    Создает тестовый клиент для API и подменяет зависимость сессии БД.
    """
    # Переопределяем зависимость get_db, чтобы API использовало тестовую сессию
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Используем ASGITransport для вызова приложения напрямую без реальной сети
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Чистим переопределения после теста
    app.dependency_overrides.clear()


