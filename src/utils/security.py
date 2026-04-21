from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt

from settings import settings
from starlette.responses import Response

def _normalize_pem_from_env(value: str) -> str:
    return value.replace("\\n", "\n").strip()


def _read_key_file(path: Path) -> str:
    if path.exists():
        return path.read_text().strip()
    return ""


def _load_jwt_keys() -> tuple[str, str]:
    private_key_env = _normalize_pem_from_env(settings.JWT_PRIVATE_KEY_PEM)
    public_key_env = _normalize_pem_from_env(settings.JWT_PUBLIC_KEY_PEM)
    if private_key_env and public_key_env:
        return private_key_env, public_key_env

    private_key_file = _read_key_file(settings.JWT_PRIVATE_KEY)
    public_key_file = _read_key_file(settings.JWT_PUBLIC_KEY)
    if private_key_file and public_key_file:
        return private_key_file, public_key_file

    raise RuntimeError(
        "JWT keys are missing. Set JWT_PRIVATE_KEY_PEM/JWT_PUBLIC_KEY_PEM env vars "
        "or provide cert files at settings.JWT_PRIVATE_KEY/settings.JWT_PUBLIC_KEY."
    )


JWT_PRIVATE_KEY, JWT_PUBLIC_KEY = _load_jwt_keys()


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
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        max_age=max_age,
        path="/",  # Cookie доступна для всего сайта
        domain=None  # None для localhost
    )