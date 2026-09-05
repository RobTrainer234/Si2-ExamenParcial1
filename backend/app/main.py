import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.audit.router import router as audit_router
from app.modules.catalog_masters.router import router as catalog_masters_router
from app.modules.catalog.router import router as catalog_router
from app.modules.locations.router import router as locations_router
from app.modules.inventory.router import router as inventory_router
from app.modules.products.router import router as products_router
from app.modules.suppliers.router import router as suppliers_router
from app.modules.seasons.router import router as seasons_router
from app.modules.system.router import router as system_router
from app.modules.users.router import router as users_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de FashionStore para el Ciclo 1.",
)
Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(system_router)
app.include_router(system_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(audit_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(locations_router, prefix=settings.api_v1_prefix)
app.include_router(catalog_masters_router, prefix=settings.api_v1_prefix)
app.include_router(suppliers_router, prefix=settings.api_v1_prefix)
app.include_router(seasons_router, prefix=settings.api_v1_prefix)
app.include_router(products_router, prefix=settings.api_v1_prefix)
app.include_router(inventory_router, prefix=settings.api_v1_prefix)
app.include_router(catalog_router, prefix=settings.api_v1_prefix)
logger.info("FashionStore API started in %s environment", settings.app_env)
