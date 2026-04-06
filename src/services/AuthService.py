import logging
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Импорты по твоим файлам [cite: 1]
from src.utils.security import get_password_hash, create_token, verify_password
from src.db.models import User
from src.db.schemas.User import UserCreate, UserLogin
from src.db.repositories.UserRepositories import (
    read_user_by_id,
    read_user_by_email,
    read_user_by_internal_id,
)

logger = logging.getLogger(__name__)


def _login_401():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect login or password",
    )


async def registration(
        user_data: UserCreate,
        session: AsyncSession,
):
    logger.debug("registration: user_id=%s", user_data.user_id)

    hashed_password = get_password_hash(user_data.password)

    user_dict = user_data.model_dump()
    user_dict.pop("password")
    new_user = User(**user_dict, password_hash=hashed_password)

    try:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
    except IntegrityError:
        await session.rollback()
        logger.info("registration: conflict, user_id=%s", user_data.user_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this data already exists",
        )
    except Exception as e:
        await session.rollback()
        logger.exception("registration: unexpected error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e

    # Используем внутренний id для JWT (user_id может быть None, если Telegram не привязан)
    data = {
        "sub": str(new_user.id),
        "role": new_user.role,
        "is_pro": new_user.is_pro,
        "is_active": new_user.is_active,
    }
    refresh_data = {"sub": str(new_user.id)}

    try:
        token = create_token(data)
        refresh_token = create_token(refresh_data, duration=60 * 60 * 24 * 30)
    except Exception as e:
        logger.exception("registration: token creation error")
        raise HTTPException(status_code=500, detail="Internal server error") from e

    logger.info("Registration successful: user_id=%s", new_user.user_id)
    return token, refresh_token


async def login(
        login_data: UserLogin,
        session: AsyncSession,
):
    identifier = str(login_data.email)
    logger.debug("Login attempt: identifier=%s", identifier)

    user = None
    try:
        if identifier.isdigit():
            user = await read_user_by_id(int(identifier), session)

        if not user:
            user = await read_user_by_email(identifier, session)

    except Exception as e:
        logger.exception("Login failed: DB error")
        raise HTTPException(status_code=500, detail="Internal server error") from e

    if not user:
        logger.info("Login failed: user not found")
        raise _login_401()

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")


    if not verify_password(login_data.password, user.password_hash):
        logger.info("Login failed: wrong password for user_id=%s", user.user_id)
        raise _login_401()

    data = {
        "sub": str(user.id),
        "role": user.role,
        "is_pro": user.is_pro,
        "is_active": user.is_active,
    }
    refresh_data = {"sub": str(user.id)}

    token = create_token(data)
    refresh_token = create_token(refresh_data, duration=60 * 60 * 24 * 30)

    logger.info("Login successful: user_id=%s", user.user_id)
    return token, refresh_token


async def get_current_user(
        user_id: int,
        session: AsyncSession,
):
    """Получить пользователя по внутреннему ID."""
    user = await read_user_by_internal_id(user_id, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user