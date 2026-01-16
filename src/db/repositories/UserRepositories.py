from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User
from src.db.schemas.User import UserCreate, UserUpdate

async def create_user(
        user_in: UserCreate,
        session: AsyncSession
) -> User:
    data = user_in.model_dump()

    plain_password = data.pop("password")
    data["password_hash"] = f"hashed_{plain_password}"

    db_user = User(**data)
    session.add(db_user)
    await session.commit()
    return db_user


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
        user_id: int,
        user_update: UserUpdate,
        session: AsyncSession
):
    db_user = await read_user_by_id(user_id, session)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def delete_user(
        user_id: int,
        session: AsyncSession
):
    stmt = delete(User).where(User.user_id == user_id)
    await session.execute(stmt)
    await session.commit()
