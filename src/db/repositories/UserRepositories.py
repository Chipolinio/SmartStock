from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.User import User
from src.db.schemas.User import UserCreate
from src.utils.security import get_password_hash

async def create_user(user_in: UserCreate, session: AsyncSession) -> User:
    data = user_in.model_dump()
    plain_password = data.pop("password")
    data["password_hash"] = get_password_hash(plain_password)
    db_user = User(**data)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

async def read_user_by_internal_id(internal_id: int, session: AsyncSession) -> User | None:
    stmt = select(User).where(User.id == internal_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def read_user_by_id(tg_id: int, session: AsyncSession) -> User | None:
    stmt = select(User).where(User.user_id == tg_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def read_user_by_email(email: str, session: AsyncSession) -> User | None:
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_user_tg_id(email: str, tg_id: int, session: AsyncSession) -> bool:
    clear_stmt = update(User).where(User.user_id == tg_id).values(user_id=None)
    await session.execute(clear_stmt)

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    db_user = result.scalar_one_or_none()

    if not db_user:
        return False

    db_user.user_id = int(tg_id)
    await session.commit()
    await session.refresh(db_user)
    return True

async def update_user(internal_id: int, update_data: dict, session: AsyncSession) -> User | None:
    """Обновить пользователя по внутреннему ID."""
    stmt = select(User).where(User.id == internal_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(user_id: int, session: AsyncSession):
    stmt = delete(User).where(User.user_id == user_id)
    await session.execute(stmt)
    await session.commit()