from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.schemas.DataPack import FullPayload
from src.db.schemas.StockTS import StockTSCreate, StockTSResponse
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate, SalesProxyTSResponse
from src.db.schemas.PriceTS import PriceTSCreate, PriceTSResponse
from src.db.schemas.DeliveryTS import DeliveryTSCreate, DeliveryTSResponse
from src.db.schemas.SocialTS import SocialTSCreate, SocialTSResponse
from src.db.schemas.PredictedSalesTS import PredictedSalesTSCreate, PredictedSalesTSResponse

from src.db.repositories import ProductRepositories as ProductRepo
from src.db.repositories import (
    StockTSRepositories as StockRepo,
    SocialTSRepositories as SocialRepo,
    SalesProxyTSRepositories as SalesRepo,
    PriceTSRepositories as PriceRepo,
    DeliveryTSRepositories as DeliveryRepo,
    PredictedSalesTSRepositories as PredictedRepo
)



async def create_stock_ts(
    stock_in: StockTSCreate,
    session: AsyncSession
):
    try:
        stock_from_db = await StockRepo.create_stock_record(
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
        sale_from_db = await SalesRepo.create_sale_record(
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

async def create_price_ts(
    price_in: PriceTSCreate,
    session: AsyncSession
):
    try:
        price_from_db = await PriceRepo.create_price_record(
            price_in = price_in,
            session = session
        )
        await session.commit()
        price_data = PriceTSResponse.model_validate(price_from_db)
        return price_data
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Price already exists"
        )

async def create_delivery_ts(
    delivery_in: DeliveryTSCreate,
    session: AsyncSession
):
    try:
        delivery_from_db = await DeliveryRepo.create_delivery_record(
            delivery_in = delivery_in,
            session = session
        )
        await session.commit()
        delivery_data = DeliveryTSResponse.model_validate(delivery_from_db)
        return delivery_data
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delivery already exists"
        )

async def create_social_ts(
    social_in: SocialTSCreate,
    session: AsyncSession
):
    try:
        social_from_db = await SocialRepo.create_social_record(
            social_in = social_in,
            session = session
        )
        await session.commit()
        social_data = SocialTSResponse.model_validate(social_from_db)
        return social_data
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Social already exists"
        )

async def create_predicted_ts(
    predicted_in: PredictedSalesTSCreate,
    session: AsyncSession
):
    try:
        predicted_from_db = await PredictedRepo.create_predict_sales_record(
            predict_sales_in = predicted_in,
            session = session
        )
        await session.commit()
        predicted_data = PredictedSalesTSResponse.model_validate(predicted_from_db)
        return predicted_data
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Predicted already exists"
        )

async def create_stocks_bulk(
    stocks_in: list[StockTSCreate],
    session: AsyncSession
) -> list[StockTSResponse]:
    try:
        stocks_from_db = await StockRepo.create_stocks_bulk(stocks_in, session)
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
        sales_from_db = await SalesRepo.create_sales_bulk(sales_in, session)
        await session.commit()
        return [SalesProxyTSResponse.model_validate(s) for s in sales_from_db]
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Sales records already exist")

async def create_prices_bulk(
    prices_in: list[PriceTSCreate],
    session: AsyncSession
) -> list[PriceTSResponse]:
    try:
        prices_from_db = await PriceRepo.create_prices_bulk(prices_in=prices_in, session=session)
        await session.commit()
        return [PriceTSResponse.model_validate(p) for p in prices_from_db]
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Prices records already exist")

async def create_deliveries_bulk(
    deliveries_in: list[DeliveryTSCreate],
    session: AsyncSession
) -> list[DeliveryTSResponse]:
    try:
        deliveries_from_db = await DeliveryRepo.create_deliveries_bulk(deliveries_in=deliveries_in, session=session)
        await session.commit()
        return [DeliveryTSResponse.model_validate(d) for d in deliveries_from_db]
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Deliveries records already exist")

async def create_socials_bulk(
    socials_in: list[SocialTSCreate],
    session: AsyncSession
) -> list[SocialTSResponse]:
    try:
        socials_from_db = await SocialRepo.create_socials_bulk(social_in=socials_in, session=session)
        await session.commit()
        return [SocialTSResponse.model_validate(s) for s in socials_from_db]
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Socials records already exist")

async def create_predicted_sales_bulk(
    predicted_sales_in: list[PredictedSalesTSCreate],
    session: AsyncSession
) -> list[PredictedSalesTSResponse]:
    try:
        predicted_sales_from_db = await PredictedRepo.create_predict_sales_bulk(predict_sales_in=predicted_sales_in, session=session)
        await session.commit()
        return [PredictedSalesTSResponse.model_validate(p) for p in predicted_sales_from_db]
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Predicted sales records already exist")


async def process_full(data_pack: FullPayload, session: AsyncSession):
    try:
        if data_pack.products_update:
            await ProductRepo.bulk_update_products(data_pack.products_update, session)

        analytics_res = await analytics_data(data_pack.stocks, session)
        await PriceRepo.create_prices_bulk(data_pack.prices, session)
        await DeliveryRepo.create_deliveries_bulk(data_pack.deliveries, session)
        await SocialRepo.create_socials_bulk(data_pack.socials, session)

        await session.commit()

        return {
            "status": "success",
            "metadata_updated": len(data_pack.products_update) if data_pack.products_update else 0,
            "processed_stocks": analytics_res.get("stocks_processed"),
            "detected_sales": analytics_res.get("sales_detected")
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def get_stock_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> list[StockTSResponse]:

    stocks = await StockRepo.read_stocks_history(
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
    sales = await SalesRepo.read_sales_history(
        product_id=product_id,
        session=session,
        limit=limit
    )
    return [SalesProxyTSResponse.model_validate(s) for s in sales]

async def get_prices_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> list[PriceTSResponse]:
    prices = await PriceRepo.read_prices_history(
        product_id=product_id,
        session=session,
        limit=limit
    )
    return [PriceTSResponse.model_validate(p) for p in prices]

async def get_deliveries_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> list[DeliveryTSResponse]:
    deliveries = await DeliveryRepo.read_delivery_history(
        product_id=product_id,
        session=session,
        limit=limit
    )
    return [DeliveryTSResponse.model_validate(d) for d in deliveries]

async def get_socials_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> list[SocialTSResponse]:
    socials = await SocialRepo.read_socials_history(
        product_id=product_id,
        session=session,
        limit=limit
    )
    return [SocialTSResponse.model_validate(s) for s in socials]

async def get_predicted_sales_history(
    product_id: int,
    session: AsyncSession,
    limit: int = 30
) -> list[PredictedSalesTSResponse]:
    predicted_sales = await PredictedRepo.read_predict_sales_history(
        product_id=product_id,
        session=session,
        limit=limit
    )
    return [PredictedSalesTSResponse.model_validate(ps) for ps in predicted_sales]

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
    latest_stocks = await StockRepo.read_latest_stocks_for_products(product_ids, session)
    old_stocks_map = {s.product_id: s.quantity for s in latest_stocks} if latest_stocks else {}

    sales_to_create = calculate_proxy_sales(stocks_in, old_stocks_map)

    try:
        created_sales_count = 0
        if sales_to_create:
            res_sales = await SalesRepo.create_sales_bulk(sales_to_create, session)
            created_sales_count = len(res_sales)

        res_stocks = await StockRepo.create_stocks_bulk(stocks_in, session)

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
    velocity_14 = await SalesRepo.calculate_velocity_with_oos(
        product_id=product_id, days=14, session=session
    )

    latest_stock = await StockRepo.read_stock_latest(product_id, session)
    stock_qty = latest_stock.quantity if latest_stock else 0

    oos_days = int(stock_qty / velocity_14) if velocity_14 > 0 else 999

    return {
        "velocity": velocity_14,
        "current_stock": stock_qty,
        "days_to_oos": oos_days
    }