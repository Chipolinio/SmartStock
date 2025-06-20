import logging
logging.basicConfig(level=logging.DEBUG)
from fastapi import FastAPI
import uvicorn
from api.routes import router

logging.debug("Starting FastAPI app")
app = FastAPI()
app.include_router(router)

@app.get("/")
async def root():
    logging.debug("Root endpoint called")
    return {"message": "SmartStock AI MVP"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)