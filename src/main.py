import logging
logging.basicConfig(level=logging.DEBUG)
from fastapi import FastAPI
from dotenv import load_dotenv
import os

logging.debug("Loading environment variables")
load_dotenv()
db_password = os.getenv("DB_PASSWORD")

logging.debug("Starting FastAPI app")
app = FastAPI()

@app.get("/")
async def root():
    logging.debug("Root endpoint called")
    return {"message": f"SmartStock AI MVP, DB Password: {db_password}"}

