from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User

async def create_user(
        user: User,
        session: AsyncSession
) -> User:
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def read_user_by_id(
        user_id: int,
        session: AsyncSession
) -> User | None:
    stmt = (
        select(User).where(User.user_id == user_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def read_user_by_email(
    email: str,
    session: AsyncSession
) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_user(
        user: User,
        session: AsyncSession
):
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(
        user_id: int,
        session: AsyncSession
):
    stmt = delete(User).where(User.user_id == user_id)
    await session.execute(stmt)
    await session.commit()
