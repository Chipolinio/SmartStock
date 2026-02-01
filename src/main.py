from fastapi import FastAPI
from .api.router import router as main_router

from src.utils.logger import setup_logging

setup_logging()

app = FastAPI()
app.include_router(main_router)