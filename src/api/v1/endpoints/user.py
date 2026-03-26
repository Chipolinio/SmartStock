from fastapi import APIRouter, Depends, status, Response, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from starlette.responses import JSONResponse

from src.db.database import get_db
from src.db.schemas.UserFavorite import (
    UserFavoriteCreateRequest,
    UserFavoriteResponse,
    UserFavoriteBatchRequest
)
from src.db.schemas.Product import ProductResponse, ProductWithDetailsResponse
from src.db.schemas.User import UserUpdate, UserProfileResponse
from src.services import UserService as UserServiceModule
from src.services import ProductService as ProductServiceModule
from src.utils.dependencies import get_user

router = APIRouter()


@router.get("/favorites", response_model=List[ProductWithDetailsResponse])
async def read_fav_products(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить список избранных товаров с ценой и остатком."""
    return await UserServiceModule.read_user_favorites_with_details(
        internal_id=user_data["user_id"],
        session=session
    )


@router.post("/favorites", response_model=UserFavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    fav_req: UserFavoriteCreateRequest | None = None,
    wb_article: int | None = Query(None, gt=0, description="Артикул WB (если товар ещё не в БД)"),
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """
    Добавить товар в избранное.
    
    Варианты:
    - **product_id** (в body): товар уже есть в БД
    - **wb_article** (в query): товар может отсутствовать, запустится скрапер (202 Accepted)
    """
    # Если указан wb_article — используем логику со скрапером
    if wb_article:
        product, is_pending = await ProductServiceModule.add_to_favorites(
            user_id=user_data["user_id"],
            wb_article=wb_article,
            session=session
        )

        if is_pending:
            background_tasks.add_task(
                ProductServiceModule.seeding_single_product,
                wb_article,
                user_data["user_id"],
                session
            )

            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    "status": "processing",
                    "message": f"Товар {wb_article} добавлен в очередь на обработку"
                }
            )

        return product
    
    # Если указан product_id — простая логика
    if fav_req and fav_req.product_id:
        return await UserServiceModule.create_user_favorites(
            internal_id=user_data["user_id"],
            product_id=fav_req.product_id,
            session=session
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Укажите product_id (в body) или wb_article (в query)"
    )


@router.post("/favorites/batch", status_code=status.HTTP_201_CREATED)
async def create_batch_favorites(
    batch_req: UserFavoriteBatchRequest,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Массовое добавление товаров в избранное по product_id."""
    return await UserServiceModule.create_batch_favorites(
        internal_id=user_data["user_id"],
        product_ids=batch_req.product_ids,
        session=session
    )


@router.delete("/favorites/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fav_product(
    product_id: int,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Удалить товар из избранного."""
    await UserServiceModule.delete_user_favorites(
        internal_id=user_data["user_id"],
        product_id=product_id,
        session=session
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# ПРОФИЛЬ И TELEGRAM (максимально просто)
# =============================================================================

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить профиль текущего пользователя."""
    user = await UserServiceModule._get_db_user_by_internal_id(user_data["user_id"], session)
    return UserProfileResponse(email=user.email)


@router.patch("/profile", response_model=UserProfileResponse)
async def update_profile(
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Обновить профиль текущего пользователя (email, password)."""
    update_data = user_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    # Если указан пароль - хешируем его перед сохранением
    if "password" in update_data:
        from src.utils.security import get_password_hash
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))

    user = await UserServiceModule.update_user(user_data["user_id"], update_data, session)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return UserProfileResponse(email=user.email)


@router.get("/telegram/info")
async def get_telegram_info(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """
    Получить информацию о привязанном Telegram.

    Для привязки: отправить боту команду /link <my_user_id>
    """
    return await UserServiceModule.get_telegram_info(user_data["user_id"], session)


@router.post("/telegram/link", response_model=dict)
async def link_telegram(
    telegram_id: int = Query(..., description="Telegram ID пользователя"),
    user_id: int = Query(..., description="Внутренний ID пользователя на сайте"),
    session: AsyncSession = Depends(get_db)
):
    """
    Привязать Telegram к аккаунту (для бота).

    Оба параметра в query params:
    - telegram_id: Telegram ID (кто пишет боту)
    - user_id: Внутренний ID пользователя на сайте (к чему привязать)
    """
    return await UserServiceModule.link_telegram_by_bot(telegram_id, user_id, session)


@router.delete("/telegram/unlink", response_model=dict)
async def unlink_telegram(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Отвязать Telegram."""
    return await UserServiceModule.unlink_user_telegram(user_data["user_id"], session)
