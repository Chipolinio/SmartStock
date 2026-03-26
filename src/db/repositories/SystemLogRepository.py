from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, Optional

from src.db.models.SystemLog import SystemLog, TaskStatus


async def log_event(
    session: AsyncSession,
    task_name: str,
    status: TaskStatus,
    processed_count: int = 0,
    payload: dict | None = None
) -> SystemLog:
    """
    Зафиксировать событие выполнения задачи.

    Args:
        session: Сессия базы данных
        task_name: Название задачи (например, 'scraper', 'ml_pipeline')
        status: Статус выполнения (SUCCESS/ERROR)
        processed_count: Количество обработанных записей
        payload: Дополнительные данные (например, traceback ошибки)

    Returns:
        Созданный объект SystemLog
    """
    db_log = SystemLog(
        task_name=task_name,
        status=status,
        processed_count=processed_count,
        payload=payload
    )
    session.add(db_log)
    await session.flush()
    await session.refresh(db_log)
    return db_log


async def get_logs(
    session: AsyncSession,
    task_name: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    limit: int = 100,
    offset: int = 0
) -> Sequence[SystemLog]:
    """
    Получить логи с фильтрацией.
    """
    stmt = select(SystemLog).order_by(desc(SystemLog.created_at)).offset(offset).limit(limit)

    if task_name:
        stmt = stmt.where(SystemLog.task_name == task_name)
    if status:
        stmt = stmt.where(SystemLog.status == status)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_log_by_id(session: AsyncSession, log_id: int) -> SystemLog | None:
    """Получить запись лога по ID."""
    stmt = select(SystemLog).where(SystemLog.id == log_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_recent_logs(session: AsyncSession, task_name: str, limit: int = 10) -> Sequence[SystemLog]:
    """Получить последние записи лога для конкретной задачи."""
    stmt = (
        select(SystemLog)
        .where(SystemLog.task_name == task_name)
        .order_by(desc(SystemLog.created_at))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_system_logs(
    session: AsyncSession,
    limit: int = 100,
    task_name: Optional[str] = None
) -> Sequence[SystemLog]:
    """
    Получить системные логи с опциональной фильтрацией по имени задачи.
    
    Args:
        session: Сессия базы данных
        limit: Количество записей
        task_name: Имя задачи для фильтрации
        
    Returns:
        Список записей SystemLog
    """
    stmt = select(SystemLog).order_by(desc(SystemLog.created_at)).limit(limit)
    
    if task_name:
        stmt = stmt.where(SystemLog.task_name == task_name)
    
    result = await session.execute(stmt)
    return list(result.scalars().all())
