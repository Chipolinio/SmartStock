from fastapi import HTTPException, Depends
from starlette import status
from starlette.requests import Request

from src.utils.security import decode_token


async def get_user(
        request: Request,
):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        data = decode_token(token)
        try:
            user_id = data.get("sub")
        except (TypeError, ValueError):
            user_id = None
        return {
            "user_id": int(user_id) if user_id else None,
            "role": data.get("role"),
            "is_pro": data.get("is_pro"),
            "is_active": data.get("is_active"),
            }
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid parsing")


async def is_user_pro(data: dict = Depends(get_user)):
    if not data["is_pro"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    if not data["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return data


async def is_user_admin(data: dict = Depends(get_user)):
    if data.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access denied")
    if not data["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return data