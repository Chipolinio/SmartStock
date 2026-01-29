from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from starlette.status import HTTP_200_OK

from src.db.database import get_db
from src.db.schemas.StockTS import StockTSCreate, StockTSResponse
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate, SalesProxyTSResponse
from src.db.schemas.PriceTS import PriceTSCreate, PriceTSResponse
from src.db.schemas.DeliveryTS import DeliveryTSCreate, DeliveryTSResponse
from src.db.schemas.SocialTS import SocialTSCreate, SocialTSResponse
from src.db.schemas.PredictedSalesTS import PredictedSalesTSCreate, PredictedSalesTSResponse
from src.db.schemas.DataPack import FullPayload
from src.services import SalesService

router = APIRouter()

@router.post("/stock", response_model=StockTSResponse, status_code=status.HTTP_201_CREATED)
async def create_stock(
        stock: StockTSCreate,
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_stock_ts(stock_in=stock, session=session)

@router.post("/sale", response_model=SalesProxyTSResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(
        sale: SalesProxyTSCreate,
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_sales_proxy_ts(sale_in=sale, session=session)

@router.post("/price", response_model=PriceTSResponse, status_code=status.HTTP_201_CREATED)
async def create_price(
        price: PriceTSCreate,
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_price_ts(price_in=price, session=session)

@router.post("/delivery", response_model=DeliveryTSResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery(
        delivery: DeliveryTSCreate,
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_delivery_ts(delivery_in=delivery, session=session)

@router.post("/social", response_model=SocialTSResponse, status_code=status.HTTP_201_CREATED)
async def create_social(
        social: SocialTSCreate,
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_social_ts(social_in=social, session=session)

@router.post("/predicted_sale", response_model=PredictedSalesTSResponse, status_code=status.HTTP_201_CREATED)
async def create_predicted_sale(
        predicted_sale: PredictedSalesTSCreate,
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_predicted_ts(predicted_in=predicted_sale, session=session)

@router.post("/stock/bulk", response_model=List[StockTSResponse], status_code=status.HTTP_201_CREATED)
async def create_stocks_bulk(
        stocks: List[StockTSCreate],
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_stocks_bulk(stocks_in=stocks, session=session)

@router.post("/sale/bulk", response_model=List[SalesProxyTSResponse], status_code=status.HTTP_201_CREATED)
async def create_sales_bulk(
        sales: List[SalesProxyTSCreate],
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_sales_bulk(sales_in=sales, session=session)

@router.post("/price/bulk", response_model=List[PriceTSResponse], status_code=status.HTTP_201_CREATED)
async def create_prices_bulk(
        prices: List[PriceTSCreate],
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_prices_bulk(prices_in=prices, session=session)

@router.post("/delivery/bulk", response_model=List[DeliveryTSResponse], status_code=status.HTTP_201_CREATED)
async def create_deliveries_bulk(
        deliveries: List[DeliveryTSCreate],
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_deliveries_bulk(deliveries_in=deliveries, session=session)

@router.post("/social/bulk", response_model=List[SocialTSResponse], status_code=status.HTTP_201_CREATED)
async def create_socials_bulk(
        socials: List[SocialTSCreate],
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_socials_bulk(socials_in=socials, session=session)

@router.post("/predicted_sale/bulk", response_model=List[PredictedSalesTSResponse], status_code=status.HTTP_201_CREATED)
async def create_socials_bulk(
        predicted: List[PredictedSalesTSCreate],
        session: AsyncSession = Depends(get_db)
):
    return await SalesService.create_predicted_sales_bulk(predicted_sales_in=predicted, session=session)

@router.post("/full-payload", status_code=status.HTTP_200_OK)
async def process_full_data_sync(
    payload: FullPayload,
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.process_full(data_pack=payload, session=session)

@router.get("/stock/{product_id}", response_model=List[StockTSResponse])
async def get_stock_history(
    product_id: int,
    limit: int = 30,
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.get_stock_history(product_id=product_id, session=session, limit=limit)

@router.get("/sale/{product_id}", response_model=List[SalesProxyTSResponse])
async def get_sales_history(
    product_id: int,
    limit: int = 30,
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.get_sales_history(product_id=product_id, session=session, limit=limit)

@router.get("/price/{product_id}", response_model=List[PriceTSResponse])
async def get_prices_history(
    product_id: int,
    limit: int = 30,
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.get_prices_history(product_id=product_id, session=session, limit=limit)

@router.get("/delivery/{product_id}", response_model=List[DeliveryTSResponse])
async def get_deliveries_history(
    product_id: int,
    limit: int = 30,
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.get_deliveries_history(product_id=product_id, session=session, limit=limit)

@router.get("/social/{product_id}", response_model=List[SocialTSResponse])
async def get_socials_history(
    product_id: int,
    limit: int = 30,
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.get_socials_history(product_id=product_id, session=session, limit=limit)

@router.get("/predicted_sale/{product_id}", response_model=List[PredictedSalesTSResponse])
async def get_predicted_sales_history(
    product_id: int,
    limit: int = 30,
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.get_predicted_sales_history(product_id=product_id, session=session, limit=limit)


@router.post("/", status_code=HTTP_200_OK)
async def stock_and_calculate_sales(
    stocks: List[StockTSCreate] = Body(..., max_length=1000),
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.analytics_data(stocks_in=stocks, session=session)

@router.get("/analytics/{product_id}")
async def get_product_sales_analytics(
    product_id: int,
    session: AsyncSession = Depends(get_db)
):
    return await SalesService.get_product_analytics(product_id=product_id, session=session)


