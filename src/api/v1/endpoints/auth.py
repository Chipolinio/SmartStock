from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from starlette.status import HTTP_201_CREATED

from src.db.database import get_db
from src.utils.security import set_auth_token
from src.utils.dependencies import is_user_admin, get_user
from src.db.schemas.User import UserCreate, UserLogin, UserResponse
from src.services.AuthService import (
    registration as registration_service,
    login as login_service,
    get_current_user as get_current_user_service,
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/me")
async def get_current_user_info(
        session: AsyncSession = Depends(get_db),
        user_data: dict = Depends(get_user)
):
    """Получить информацию о текущем пользователе."""
    return await get_current_user_service(user_data["user_id"], session)

@router.post("/registration/", status_code=HTTP_201_CREATED)
async def registration(
        user_data: UserCreate,
        response: Response,
        session: AsyncSession = Depends(get_db)
):
    token, refresh_token = await registration_service(
        user_data=user_data,
        session=session,
    )
    set_auth_token(response, token, "access_token")
    set_auth_token(response, refresh_token, "refresh_token")
    return {"status": "success"}


@router.post(
    "/login/",
    status_code=status.HTTP_200_OK,
)
async def login(
        login_data: UserLogin,
        response: Response,
        session: AsyncSession = Depends(get_db)
):
    token, refresh_token = await login_service(
        login_data=login_data,
        session=session,
    )
    set_auth_token(response, token, "access_token", 1800)
    set_auth_token(response, refresh_token, "refresh_token", 60 * 60 * 24 * 30)
    logger.info(f"Login with data {login_data}")
    return {"status": "success"}
