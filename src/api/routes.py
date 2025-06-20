from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.database.db import Sales, get_db

router = APIRouter()

@router.get("/sales")
def get_sales(db: Session = Depends(get_db)):
    sales = db.query(Sales).all()
    return {"sales": [{"id": s.id,
                       "date": s.date,
                       "product_id": s.product_id,
                       "quantity": s.quantity,
                       "revenue": s.revenue} for s in sales]}
@router.post("/sales")
def add_sales(date: str, product_id: int, quantity: int, revenue: float, db: Session = Depends(get_db)):
    new_sale = Sales(date = date,
                     product_id = product_id,
                     quantity = quantity,
                     revenue = revenue)
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    return {"id": new_sale.id, "message": "Sale added"}