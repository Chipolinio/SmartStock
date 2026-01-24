from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from starlette.status import HTTP_200_OK

from src.db.database import get_db
from src.db.schemas.StockTS import StockTSCreate, StockTSResponse
from src.db.schemas.SalesProxyTS import SalesProxyTSCreate, SalesProxyTSResponse
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


