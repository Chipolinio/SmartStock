import logging

from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from src.database.db import Sales, Forecasts, get_db

from fastapi import FastAPI, Request
import uvicorn
from api.routes import router

logging.basicConfig(level=logging.DEBUG)


logging.debug("Starting FastAPI app")
app = FastAPI()
app.include_router(router)

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root():
    logging.debug("Root endpoint called")
    return {"message": "SmartStock AI MVP"}

@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    logging.debug("Dashboard endpoint called")
    sales = db.query(Sales).order_by(Sales.date).limit(10).all()
    forecasts = db.query(Forecasts).order_by(Forecasts.date).limit(10).all()
    sales_data = [(s.date.strftime("%Y-%m-%d"), s.revenue) for s in sales]
    forecast_data = [(f.date.strftime("%Y-%m-%d"), f.predicted_quantity) for f in forecasts]
    total_revenue = db.query(Sales).with_entities(Sales.revenue).all()
    avg_predicted = db.query(Forecasts).with_entities(Forecasts.predicted_quantity).all()
    total_revenue_sum = sum(r[0] for r in total_revenue) if total_revenue else 0
    avg_predicted_mean = sum(p[0] for p in avg_predicted) / len(avg_predicted) if avg_predicted else 0
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": "Панель управления SmartStock AI",
        "sales": sales,
        "forecasts": forecasts,
        "sales_data": sales_data,
        "forecast_data": forecast_data,
        "total_revenue": total_revenue_sum,
        "avg_predicted": avg_predicted_mean
    })

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)