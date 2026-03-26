from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from settings import settings
from starlette.responses import Response

JWT_PRIVATE_KEY = settings.JWT_PRIVATE_KEY.read_text()
JWT_PUBLIC_KEY = settings.JWT_PUBLIC_KEY.read_text()


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_token(data_dict: dict, duration: int = 1800) -> str:
    data = data_dict.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=duration)
    data.update({"exp": expire})
    return jwt.encode(data, JWT_PRIVATE_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[settings.ALGORITHM,])


def set_auth_token(response: Response, token: str, key: str, max_age: int = 1800):
    response.set_cookie(
        key=key,
        value=token,
        httponly=True,
        samesite="lax",  # Или "none" для кросс-доменных запросов
        secure=False,  # False для HTTP (localhost)
        max_age=max_age,
        path="/",  # Cookie доступна для всего сайта
        domain=None  # None для localhost
    )