from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.router import router
from src.utils.logger import setup_logging
from src.services.TaskSchedulerService import TaskSchedulerService

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = TaskSchedulerService()
    scheduler.start()

    #app.state.scheduler = scheduler
    yield
    # При выключении (если нужно что-то закрыть)
    # scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(router)