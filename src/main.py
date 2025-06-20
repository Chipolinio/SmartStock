import logging

from fastapi.params import Depends
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates

from src.database.db import Sales, Forecasts, get_db

from fastapi import FastAPI, Request
import uvicorn
from api.routes import router

logging.basicConfig(level=logging.DEBUG)


logging.debug("Starting FastAPI app")
app = FastAPI()
app.include_router(router)

templates = Jinja2Templates(directory="src/templates")

@app.get("/")
async def root():
    logging.debug("Root endpoint called")
    return {"message": "SmartStock AI MVP"}

@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    logging.debug("Dashboard endpoint called")
    sales = db.query(Sales).limit(5).all()
    forecasts = db.query(Forecasts).limit(5).all()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": "SmartStock AI Dashboard",
        "sales": sales,
        "forecasts": forecasts
    })

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)