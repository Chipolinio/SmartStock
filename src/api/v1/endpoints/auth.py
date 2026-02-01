from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from starlette.status import HTTP_201_CREATED

from src.db.database import get_db
from src.utils.security import set_auth_token
from src.utils.dependencies import is_user_admin
from src.db.schemas.User import UserCreate, UserLogin
from src.services import AuthService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/registration/", status_code=HTTP_201_CREATED)
async def registration(
        user_data: UserCreate,
        response: Response,
        session: AsyncSession = Depends(get_db)
):
    token, refresh_token = await AuthService.registration(
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
    token, refresh_token = await AuthService.login(
        login_data=login_data,
        session=session,
    )
    set_auth_token(response, token, "access_token", 1800)
    set_auth_token(response, refresh_token, "refresh_token", 60 * 60 * 24 * 30)
    logger.info(f"Login with data {login_data}")
    return {"status": "success"}
