from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.schemas.StockTS import StockTSCreate, StockTSResponse
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate, SalesProxyTSResponse
from src.db.repositories import StockTSRepositories
from src.db.repositories import SalesProxyTSRepositories


async def create_stock_ts(
    stock_in: StockTSCreate,
    session: AsyncSession
):
    try:
        stock_from_db = await StockTSRepositories.create_stock_record(
            stock_in = stock_in,
            session = session
        )
        await session.commit()
        stock_data = StockTSResponse.model_validate(stock_from_db)
        return stock_data
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stock already exists"
        )

async def create_sales_proxy_ts(
    sale_in: SalesProxyTSCreate,
    session: AsyncSession
) -> SalesProxyTSResponse:
    try:
        sale_from_db = await SalesProxyTSRepositories.create_sale_record(
            sale_in=sale_in,
            session=session
        )
        await session.commit()
        return SalesProxyTSResponse.model_validate(sale_from_db)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Sales record for this date already exists"
        )

async def create_stocks_bulk(
    stocks_in: list[StockTSCreate],
    session: AsyncSession
) -> list[StockTSResponse]:
    try:
        stocks_from_db = await StockTSRepositories.create_stocks_bulk(stocks_in, session)
        await session.commit()
        return [StockTSResponse.model_validate(s) for s in stocks_from_db]
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Stock records already exist")

async def create_sales_bulk(
    sales_in: list[SalesProxyTSCreate],
    session: AsyncSession
) -> list[SalesProxyTSResponse]:
    try:
        sales_from_db = await SalesProxyTSRepositories.create_sales_bulk(sales_in, session)
        await session.commit()
        return [SalesProxyTSResponse.model_validate(s) for s in sales_from_db]
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Sales records already exist")

async def get_stock_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> list[StockTSResponse]:

    stocks = await StockTSRepositories.read_stocks_history(
        product_id=product_id,
        session=session,
        limit=limit
    )
    return [StockTSResponse.model_validate(s) for s in stocks]

async def get_sales_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> list[SalesProxyTSResponse]:
    sales = await SalesProxyTSRepositories.read_sales_history(
        product_id=product_id,
        session=session,
        limit=limit
    )
    return [SalesProxyTSResponse.model_validate(s) for s in sales]

def calculate_proxy_sales(
        stocks_in: list[StockTSCreate],
        old_stocks_map: dict[int, int],
        confidence: float = 0.85
) -> list[SalesProxyTSCreate]:
    sales_to_create = []
    for new_stock in stocks_in:
        prev_qty = old_stocks_map.get(new_stock.product_id)

        if prev_qty is None:
            continue

        delta = prev_qty - new_stock.quantity
        if delta > 0:
            sales_to_create.append(SalesProxyTSCreate(
                product_id=new_stock.product_id,
                dt=new_stock.dt,
                sales=delta,
                confidence=confidence
            ))
    return sales_to_create


async def analytics_data(
        stocks_in: list[StockTSCreate],
        session: AsyncSession
) -> dict:
    if not stocks_in:
        return {"status": "skipped", "detail": "Empty stock list"}
    product_ids = list({s.product_id for s in stocks_in})
    latest_stocks = await StockTSRepositories.read_latest_stocks_for_products(product_ids, session)
    old_stocks_map = {s.product_id: s.quantity for s in latest_stocks} if latest_stocks else {}

    sales_to_create = calculate_proxy_sales(stocks_in, old_stocks_map)

    try:
        created_sales_count = 0
        if sales_to_create:
            res_sales = await SalesProxyTSRepositories.create_sales_bulk(sales_to_create, session)
            created_sales_count = len(res_sales)

        res_stocks = await StockTSRepositories.create_stocks_bulk(stocks_in, session)

        await session.commit()

        return {
            "status": "success",
            "stocks_processed": len(res_stocks),
            "sales_detected": created_sales_count
        }
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Data conflict. Use specific update methods.")


async def get_product_analytics(
        product_id: int,
        session: AsyncSession
) -> dict:
    velocity_14 = await SalesProxyTSRepositories.calculate_velocity_with_oos(
        product_id=product_id, days=14, session=session
    )

    latest_stock = await StockTSRepositories.read_stock_latest(product_id, session)
    stock_qty = latest_stock.quantity if latest_stock else 0

    oos_days = int(stock_qty / velocity_14) if velocity_14 > 0 else 999

    return {
        "velocity": velocity_14,
        "current_stock": stock_qty,
        "days_to_oos": oos_days
    }