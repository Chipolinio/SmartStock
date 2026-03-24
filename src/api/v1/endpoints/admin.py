from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.db.database import get_db
from src.db.schemas.Product import ProductCreate, ProductUpdate, ProductResponse
from src.db.schemas.StockTS import StockTSCreate, StockTSResponse
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate, SalesProxyTSResponse
from src.db.schemas.PriceTS import PriceTSCreate, PriceTSResponse
from src.db.schemas.DeliveryTS import DeliveryTSCreate, DeliveryTSResponse
from src.db.schemas.SocialTS import SocialTSCreate, SocialTSResponse
from src.db.schemas.PredictedSalesTS import PredictedSalesTSCreate, PredictedSalesTSResponse
from src.db.schemas.DataPack import FullPayload
from src.db.schemas.SystemLog import SystemLogResponse, TaskAcceptedResponse
from src.services import (
    ProductService as ProductServiceModule,
    SalesService as SalesServiceModule,
    MLService as MLServiceModule
)
from src.utils.dependencies import is_user_admin

router = APIRouter(dependencies=[Depends(is_user_admin)])


# =============================================================================
# PRODUCTS ADMIN (POST/PATCH/DELETE)
# =============================================================================

@router.post("/products/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_product(
    product: ProductCreate,
    session: AsyncSession = Depends(get_db)
):
    """Создать товар (админ)."""
    return await ProductServiceModule.create_product(product=product, session=session)


@router.post("/products/bulk", response_model=List[ProductResponse], status_code=status.HTTP_201_CREATED)
async def admin_create_products_bulk(
    products: List[ProductCreate],
    session: AsyncSession = Depends(get_db)
):
    """Массовое создание товаров (админ)."""
    return await ProductServiceModule.create_products_bulk(products=products, session=session)


@router.patch("/products/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def admin_update_product(
    product_id: int,
    product_in: ProductUpdate,
    session: AsyncSession = Depends(get_db)
):
    """Обновить товар (админ)."""
    return await ProductServiceModule.update_product(
        product_id=product_id,
        product=product_in,
        session=session
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_db)
):
    """Удалить товар (админ)."""
    await ProductServiceModule.delete_product(product_id=product_id, session=session)
    return None


# =============================================================================
# SALES ADMIN (POST - создание time series данных)
# =============================================================================

@router.post("/sales/stock", response_model=StockTSResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_stock(
    stock: StockTSCreate,
    session: AsyncSession = Depends(get_db)
):
    """Создать запись остатков (админ)."""
    return await SalesServiceModule.create_stock_ts(stock_in=stock, session=session)


@router.post("/sales/stock/bulk", response_model=List[StockTSResponse], status_code=status.HTTP_201_CREATED)
async def admin_create_stocks_bulk(
    stocks: List[StockTSCreate],
    session: AsyncSession = Depends(get_db)
):
    """Массовое создание записей остатков (админ)."""
    return await SalesServiceModule.create_stocks_bulk(stocks_in=stocks, session=session)


@router.post("/sales/sale", response_model=SalesProxyTSResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_sale(
    sale: SalesProxyTSCreate,
    session: AsyncSession = Depends(get_db)
):
    """Создать запись продаж (админ)."""
    return await SalesServiceModule.create_sales_proxy_ts(sale_in=sale, session=session)


@router.post("/sales/sale/bulk", response_model=List[SalesProxyTSResponse], status_code=status.HTTP_201_CREATED)
async def admin_create_sales_bulk(
    sales: List[SalesProxyTSCreate],
    session: AsyncSession = Depends(get_db)
):
    """Массовое создание записей продаж (админ)."""
    return await SalesServiceModule.create_sales_bulk(sales_in=sales, session=session)


@router.post("/sales/price", response_model=PriceTSResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_price(
    price: PriceTSCreate,
    session: AsyncSession = Depends(get_db)
):
    """Создать запись цены (админ)."""
    return await SalesServiceModule.create_price_ts(price_in=price, session=session)


@router.post("/sales/price/bulk", response_model=List[PriceTSResponse], status_code=status.HTTP_201_CREATED)
async def admin_create_prices_bulk(
    prices: List[PriceTSCreate],
    session: AsyncSession = Depends(get_db)
):
    """Массовое создание записей цен (админ)."""
    return await SalesServiceModule.create_prices_bulk(prices_in=prices, session=session)


@router.post("/sales/delivery", response_model=DeliveryTSResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_delivery(
    delivery: DeliveryTSCreate,
    session: AsyncSession = Depends(get_db)
):
    """Создать запись доставки (админ)."""
    return await SalesServiceModule.create_delivery_ts(delivery_in=delivery, session=session)


@router.post("/sales/delivery/bulk", response_model=List[DeliveryTSResponse], status_code=status.HTTP_201_CREATED)
async def admin_create_deliveries_bulk(
    deliveries: List[DeliveryTSCreate],
    session: AsyncSession = Depends(get_db)
):
    """Массовое создание записей доставки (админ)."""
    return await SalesServiceModule.create_deliveries_bulk(deliveries_in=deliveries, session=session)


@router.post("/sales/social", response_model=SocialTSResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_social(
    social: SocialTSCreate,
    session: AsyncSession = Depends(get_db)
):
    """Создать запись социальных данных (админ)."""
    return await SalesServiceModule.create_social_ts(social_in=social, session=session)


@router.post("/sales/social/bulk", response_model=List[SocialTSResponse], status_code=status.HTTP_201_CREATED)
async def admin_create_socials_bulk(
    socials: List[SocialTSCreate],
    session: AsyncSession = Depends(get_db)
):
    """Массовое создание записей социальных данных (админ)."""
    return await SalesServiceModule.create_socials_bulk(socials_in=socials, session=session)


# =============================================================================
# FULL PAYLOAD ADMIN (синхронная обработка полного пакета данных)
# =============================================================================

@router.post("/sales/full-payload", status_code=status.HTTP_200_OK)
async def admin_process_full_data(
    payload: FullPayload,
    session: AsyncSession = Depends(get_db)
):
    """
    Обработать полный пакет данных (products + stocks + prices + deliveries + socials).
    
    Используется для синхронной загрузки данных от внешнего скрапера.
    """
    return await SalesServiceModule.process_full(data_pack=payload, session=session)


@router.post("/sales/analytics", status_code=status.HTTP_200_OK)
async def admin_stock_and_calculate_sales(
    stocks: List[StockTSCreate] = Body(..., max_length=1000),
    session: AsyncSession = Depends(get_db)
):
    """
    Загрузить остатки и автоматически рассчитать продажи.
    
    Принимает список остатков, сравнивает с предыдущими значениями
    и создаёт записи продаж (разница остатков).
    """
    return await SalesServiceModule.analytics_data(stocks_in=stocks, session=session)


# =============================================================================
# SCRAPER ADMIN
# =============================================================================

@router.post("/scraper/run", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def admin_run_scraper(
    article: int,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db)
):
    """
    Запустить скрапер для добавления товара по артикулу.

    Товар добавляется в фоновом режиме.
    """
    from src.services.ProductService import seeding_single_product

    # Запускаем скрапер без привязки к пользователю (только данные)
    background_tasks.add_task(seeding_single_product, article, 0, session)

    return TaskAcceptedResponse(
        status="accepted",
        message=f"Скрапер запущен для артикула {article}"
    )


# =============================================================================
# ML ADMIN
# =============================================================================

@router.post("/ml/train", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def admin_run_model_training(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db)
):
    """
    Запустить переобучение ML-модели.

    Процесс выполняется в фоновом режиме.
    """
    background_tasks.add_task(MLServiceModule.run_model_training, session)

    return TaskAcceptedResponse(
        status="accepted",
        message="Обучение модели запущено"
    )


@router.post("/ml/forecast", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def admin_run_daily_forecast(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db)
):
    """
    Запустить ежедневный прогноз продаж.

    Процесс выполняется в фоновом режиме.
    """
    from datetime import date
    background_tasks.add_task(MLServiceModule.run_daily_forecast, session, date.today())

    return TaskAcceptedResponse(
        status="accepted",
        message="Прогноз продаж запущен"
    )


# =============================================================================
# SYSTEM LOGS
# =============================================================================

@router.get("/logs", response_model=List[SystemLogResponse])
async def admin_get_system_logs(
    limit: int = Query(default=100, ge=1, le=1000, description="Количество записей"),
    task_name: str | None = Query(None, description="Фильтр по имени задачи"),
    session: AsyncSession = Depends(get_db)
):
    """Получить системные логи."""
    from src.db.repositories.SystemLogRepository import get_system_logs
    
    logs = await get_system_logs(
        session=session,
        limit=limit,
        task_name=task_name
    )
    
    return [SystemLogResponse.model_validate(log) for log in logs]
