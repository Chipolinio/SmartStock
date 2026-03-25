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
from src.db.schemas.Product import ProductResponse
from src.db.schemas.User import UserResponse, UserUpdate
from src.services import UserService as UserServiceModule
from src.services import ProductService as ProductServiceModule
from src.utils.dependencies import get_user

router = APIRouter()


@router.get("/favorites", response_model=List[ProductResponse])
async def read_fav_products(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить список избранных товаров."""
    return await UserServiceModule.read_user_favorites(
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

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Получить профиль текущего пользователя."""
    from src.db.repositories.UserRepositories import read_user_by_internal_id
    user = await read_user_by_internal_id(user_data["user_id"], session)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Обновить профиль текущего пользователя."""
    from src.db.repositories.UserRepositories import update_user

    # Разрешаем обновлять только user_id (Telegram ID)
    update_data = user_update.model_dump(exclude_unset=True)
    if "email" in update_data or "role" in update_data or "is_pro" in update_data or "is_active" in update_data:
        raise HTTPException(status_code=403, detail="Нельзя обновлять это поле")

    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")

    user = await update_user(user_data["user_id"], update_data, session)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return UserResponse.model_validate(user)


@router.get("/telegram/info")
async def get_telegram_info(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """
    Получить информацию о привязанном Telegram.

    Для привязки: отправить боту команду /link <my_user_id>
    """
    from src.db.repositories.UserRepositories import read_user_by_internal_id

    user = await read_user_by_internal_id(user_data["user_id"], session)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    return {
        "telegram_id": user.user_id,
        "is_linked": user.user_id is not None,
        "my_user_id": user.id  # Этот ID нужно отправить боту: /link <my_user_id>
    }


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
    from sqlalchemy import select
    from src.db.models.User import User
    
    # Проверяем, не привязан ли уже этот TG
    check_stmt = select(User).where(
        User.user_id == telegram_id,
        User.id != user_id
    )
    check_result = await session.execute(check_stmt)
    existing = check_result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Этот Telegram уже привязан к другому аккаунту"
        )
    
    # Привязываем
    from src.db.repositories.UserRepositories import update_user
    user = await update_user(user_id, {"user_id": telegram_id}, session)
    
    return {"status": "success", "message": "Telegram привязан", "telegram_id": telegram_id}


@router.delete("/telegram/unlink", response_model=dict)
async def unlink_telegram(
    session: AsyncSession = Depends(get_db),
    user_data: dict = Depends(get_user)
):
    """Отвязать Telegram."""
    from src.db.repositories.UserRepositories import update_user
    
    user = await update_user(user_data["user_id"], {"user_id": None}, session)
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    
    return {"status": "success", "message": "Telegram отвязан"}
