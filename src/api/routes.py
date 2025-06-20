# D:\SmartStock\src\api\routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database.db import get_db, Sales, Forecasts
from src.schemas.models import SaleCreate, SaleUpdate, ForecastCreate, ForecastUpdate
from datetime import date

router = APIRouter()

@router.get("/sales", summary="Get all sales", description="Retrieve all sales records with filtering by date.")
def get_sales(date: str = None, db: Session = Depends(get_db)):
    query = db.query(Sales)  # Инициализация запроса
    if date:
        try:
            query = query.filter(Sales.date == date)  # Фильтрация по дате
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    sales = query.all()  # Выполнение запроса
    return {"sales": [{"id": s.id, "date": s.date, "product_id": s.product_id, "product_name": s.product_name, "quantity": s.quantity, "revenue": s.revenue, "store_id": s.store_id} for s in sales]}

@router.post("/sales", summary="Add a new sale", description="Create a new sales record.")
def add_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    try:
        new_sale = Sales(**sale.dict())
        db.add(new_sale)
        db.commit()
        db.refresh(new_sale)
        return {"id": new_sale.id, "message": "Sale added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding sale: {str(e)}")

@router.put("/sales/{sale_id}", summary="Update a sale", description="Update an existing sales record by ID.")
def update_sale(sale_id: int, sale: SaleUpdate, db: Session = Depends(get_db)):
    db_sale = db.query(Sales).filter(Sales.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    update_data = sale.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sale, key, value)
    db.commit()
    db.refresh(db_sale)
    return {"id": db_sale.id, "message": "Sale updated"}

@router.delete("/sales/{sale_id}", summary="Delete a sale", description="Delete a sales record by ID.")
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    db_sale = db.query(Sales).filter(Sales.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    db.delete(db_sale)
    db.commit()
    return {"message": "Sale deleted"}

@router.get("/forecasts", summary="Get all forecasts", description="Retrieve all forecast records with filtering by date.")
def get_forecasts(date: str = None, db: Session = Depends(get_db)):
    query = db.query(Forecasts)
    if date:
        try:
            query = query.filter(Forecasts.date == date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    forecasts = query.all()
    return {"forecasts": [{"id": f.id, "date": f.date, "product_id": f.product_id, "product_name": f.product_name, "predicted_quantity": f.predicted_quantity, "confidence": f.confidence, "forecast_method": f.forecast_method, "created_at": f.created_at} for f in forecasts]}

@router.post("/forecasts", summary="Add a new forecast", description="Create a new forecast record.")
def add_forecast(forecast: ForecastCreate, db: Session = Depends(get_db)):
    try:
        new_forecast = Forecasts(**forecast.dict())
        db.add(new_forecast)
        db.commit()
        db.refresh(new_forecast)
        return {"id": new_forecast.id, "message": "Forecast added"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding forecast: {str(e)}")

@router.put("/forecasts/{forecast_id}", summary="Update a forecast", description="Update an existing forecast record by ID.")
def update_forecast(forecast_id: int, forecast: ForecastUpdate, db: Session = Depends(get_db)):
    db_forecast = db.query(Forecasts).filter(Forecasts.id == forecast_id).first()
    if not db_forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    update_data = forecast.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_forecast, key, value)
    db.commit()
    db.refresh(db_forecast)
    return {"id": db_forecast.id, "message": "Forecast updated"}

@router.delete("/forecasts/{forecast_id}", summary="Delete a forecast", description="Delete a forecast record by ID.")
def delete_forecast(forecast_id: int, db: Session = Depends(get_db)):
    db_forecast = db.query(Forecasts).filter(Forecasts.id == forecast_id).first()
    if not db_forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")
    db.delete(db_forecast)
    db.commit()
    return {"message": "Forecast deleted"}

@router.get("/analytics", summary="Get sales analytics", description="Retrieve total revenue and average predicted quantity.")
def get_analytics(db: Session = Depends(get_db)):
    total_revenue = db.query(Sales).with_entities(Sales.revenue).all()
    avg_predicted = db.query(Forecasts).with_entities(Forecasts.predicted_quantity).all()
    total_revenue_sum = sum(r[0] for r in total_revenue) if total_revenue else 0
    avg_predicted_mean = sum(p[0] for p in avg_predicted) / len(avg_predicted) if avg_predicted else 0
    return {
        "total_revenue": total_revenue_sum,
        "average_predicted_quantity": avg_predicted_mean
    }