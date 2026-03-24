import logging
from typing import Optional, Tuple, List
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.schemas.Product import ProductCreate, ProductUpdate, ProductResponse
from src.db.repositories import ProductRepositories as ProductRepo
from src.db.repositories import UserFavoriteRepositories as UserFavoriteRepo
from src.db.schemas.UserFavorite import UserFavoriteCreate
from src.services.IntegrationService import WBScraper
from src.services import SalesService as SalesServiceModule

logger = logging.getLogger(__name__)


async def create_product(product: ProductCreate, session: AsyncSession):
    try:
        product_from_db = await ProductRepo.create_product(
            product_in = product,
            session = session
        )
        await session.commit()
        product_data = ProductResponse.model_validate(product_from_db)
        return product_data
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product already exists")


async def create_products_bulk(products: list[ProductCreate], session: AsyncSession):
    try:
        products_form_db = await ProductRepo.bulk_upsert_products(
            products_in=products,
            session=session)
        await session.commit()
        return [ProductResponse.model_validate(p) for p in products_form_db]
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Products records already exist")


async def get_product_by_id(product_id: int, session: AsyncSession):
    product_from_db = await ProductRepo.read_product(
        product_id = product_id,
        session = session
    )
    if not product_from_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    product_data = ProductResponse.model_validate(product_from_db)
    return product_data


async def get_products_filter(
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        name: str | None = None,
        brand: str | None = None,
        subject: str | None = None,
        entity: str | None = None
):
    products_from_db = await ProductRepo.read_products(
        session = session,
        skip = skip,
        limit = limit,
        name = name,
        brand = brand,
        subject = subject,
        entity = entity
    )
    product_data = [ProductResponse.model_validate(product) for product in products_from_db]
    return product_data


async def update_product(
        product_id: int,
        product: ProductUpdate,
        session: AsyncSession
):
    try:
        updated = await ProductRepo.update_product(
            product_id=product_id,
            product_update=product,
            session=session
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Product not found")
        return ProductResponse.model_validate(updated)

    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Conflict: Check your data")


async def delete_product(product_id: int, session: AsyncSession):
    product_from_db = await ProductRepo.read_product(
        product_id=product_id,
        session=session
    )
    if not product_from_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    await ProductRepo.delete_product(
        product_id=product_id,
        session=session
    )
    return {"detail": "Product deleted successfully"}


# =============================================================================
# ИЗБРАННОЕ (Favorites) — с поддержкой 202 Accepted
# =============================================================================

async def add_to_favorites(
    user_id: int,
    wb_article: int,
    session: AsyncSession
) -> Tuple[Optional[ProductResponse], bool]:
    """
    Добавить товар в избранное.
    
    Returns:
        Tuple[ProductResponse | None, bool]:
            - (product, False) — товар найден в БД, готов к отдаче (201 Created)
            - (None, True) — товар не найден, запущен скрапер (202 Accepted)
    """
    # 1. Проверяем, есть ли товар в БД
    product = await ProductRepo.get_by_article(wb_article, session)
    
    if product:
        # Товар найден — просто добавляем в избранное
        fav_in = UserFavoriteCreate(user_id=user_id, product_id=wb_article)
        result = await UserFavoriteRepo.create_user_favorites(fav_in, session)
        
        if not result:
            # Уже в избранном
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product already in favorites"
            )
        
        await session.commit()
        return ProductResponse.model_validate(product), False
    
    # 2. Товара нет в БД — запускаем скрапер (возвращаем Pending статус)
    logger.info(f"Product {wb_article} not found, initiating scraper for user {user_id}")
    
    # Возвращаем Pending статус — скрапер будет запущен отдельно
    return None, True


async def seeding_single_product(
    wb_article: int,
    user_id: int,
    session: AsyncSession
) -> ProductResponse:
    """
    Монолитный сидер + добавление в избранное.
    Скачивает данные по артикулу, сохраняет в БД и добавляет в избранное.
    Используется в background task при добавлении товара которого нет в БД.
    """
    scraper = WBScraper()
    
    try:
        # Скачиваем данные по одному артикулу
        data_pack = await scraper.fetch_data([wb_article])
        
        if not data_pack.products_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found on Wildberries"
            )
        
        # Сохраняем ВСЕ данные (products + _TS таблицы)
        result = await SalesServiceModule.process_full(data_pack, session)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save product data"
            )
        
        # Добавляем товар в избранное пользователя
        fav_in = UserFavoriteCreate(user_id=user_id, product_id=wb_article)
        await UserFavoriteRepo.create_user_favorites(fav_in, session)
        
        await session.commit()
        
        logger.info(f"Product {wb_article} seeded and added to favorites for user {user_id}")

        # Возвращаем сохранённый товар
        product = await ProductRepo.get_by_article(wb_article, session)
        return ProductResponse.model_validate(product)

    except Exception as e:
        logger.error(f"Seeding error for article {wb_article}: {e}")
        await session.rollback()
        raise


async def add_batch_to_favorites(
    user_id: int,
    wb_articles: List[int],
    session: AsyncSession
) -> dict:
    """
    Массовое добавление товаров в избранное.
    
    Returns:
        {
            "added": [...],  # Товары, добавленные сразу
            "pending": [...],  # Товары в обработке (скрапер)
            "already_in_favorites": [...]  # Уже в избранном
        }
    """
    from src.services.Seeder import seed_articles_batch
    
    result = {
        "added": [],
        "pending": [],
        "already_in_favorites": []
    }
    
    # 1. Проверяем, какие товары есть в БД
    existing_products = []
    missing_articles = []
    
    for article in wb_articles:
        product = await ProductRepo.get_by_article(article, session)
        if product:
            existing_products.append(product)
        else:
            missing_articles.append(article)
    
    # 2. Создаём заглушки для отсутствующих товаров
    if missing_articles:
        logger.info(f"Creating stubs for {len(missing_articles)} products...")
        await seed_articles_batch(missing_articles, session)
    
    # 3. Добавляем все товары в избранное
    for article in wb_articles:
        fav_in = UserFavoriteCreate(user_id=user_id, product_id=article)
        fav_result = await UserFavoriteRepo.create_user_favorites(fav_in, session)
        
        if fav_result:
            if article in missing_articles:
                result["pending"].append(article)
            else:
                result["added"].append(article)
        else:
            result["already_in_favorites"].append(article)
    
    await session.commit()
    
    logger.info(f"Batch favorites for user {user_id}: added={len(result['added'])}, pending={len(result['pending'])}, exists={len(result['already_in_favorites'])}")
    
    return result