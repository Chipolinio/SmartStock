import logging
logging.basicConfig(level=logging.DEBUG)
from fastapi import FastAPI

logging.debug("Starting FastAPI app")
app = FastAPI()

@app.get("/")
async def root():
    logging.debug("Root endpoint called")
    return {"message": "SmartStock AI MVP"}