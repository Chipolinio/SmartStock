from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
import os
from src.api.router import router
from src.utils.logger import setup_logging
from src.services.TaskSchedulerService import TaskSchedulerService

setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = TaskSchedulerService()
    scheduler.start()
    yield

app = FastAPI(lifespan=lifespan)

# CORS middleware (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы (фронтенд и лендинг)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(BASE_DIR, "frontend")
landing_dir = os.path.join(BASE_DIR, "landing")

# Класс для отдачи статики лендинга без кеширования
class LandingStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if isinstance(response, Response):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
app.mount("/landing-assets", LandingStaticFiles(directory=os.path.join(landing_dir, "public")), name="landing-assets")

# Хелпер для отдачи HTML без кеширования
def html_no_cache(path: str) -> FileResponse:
    resp = FileResponse(path)
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

# Маршруты для страниц (ДО API роутов!)
@app.get("/")
async def root():
    return html_no_cache(os.path.join(landing_dir, "index.html"))

@app.get("/login")
async def login_page():
    return html_no_cache(os.path.join(frontend_dir, "login.html"))

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse(os.path.join(frontend_dir, "dashboard.html"))

@app.get("/products")
async def products_page():
    return FileResponse(os.path.join(frontend_dir, "products.html"))

@app.get("/favorites")
async def favorites_page():
    return FileResponse(os.path.join(frontend_dir, "favorites.html"))

@app.get("/product_analytics")
async def product_analytics_page():
    return FileResponse(os.path.join(frontend_dir, "product_analytics.html"))

@app.get("/profile")
async def profile_page():
    return FileResponse(os.path.join(frontend_dir, "profile.html"))

@app.get("/telegram")
async def telegram_page():
    return FileResponse(os.path.join(frontend_dir, "telegram.html"))

@app.get("/admin")
async def admin_page():
    return FileResponse(os.path.join(frontend_dir, "admin.html"))

@app.get("/forecasts")
async def forecasts_page():
    return FileResponse(os.path.join(frontend_dir, "forecasts.html"))

@app.get("/analytics-sales")
async def analytics_sales_page():
    return FileResponse(os.path.join(frontend_dir, "analytics-sales.html"))

@app.get("/analytics-stock")
async def analytics_stock_page():
    return FileResponse(os.path.join(frontend_dir, "analytics-stock.html"))

@app.get("/analytics-abc")
async def analytics_abc_page():
    return FileResponse(os.path.join(frontend_dir, "analytics-abc.html"))

@app.get("/analytics-xyz")
async def analytics_xyz_page():
    return FileResponse(os.path.join(frontend_dir, "analytics-xyz.html"))

@app.get("/analytics-tops")
async def analytics_tops_page():
    return FileResponse(os.path.join(frontend_dir, "analytics-tops.html"))

@app.get("/reports-builder")
async def reports_builder_page():
    return FileResponse(os.path.join(frontend_dir, "reports-builder.html"))

# API роуты (ПОСЛЕ страниц!)
app.include_router(router)
