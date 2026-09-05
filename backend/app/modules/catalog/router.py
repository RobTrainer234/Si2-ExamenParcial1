from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.catalog import service
from app.modules.catalog.schemas import AvailabilityItem, CatalogDetail, CatalogFilters, CatalogNavigation, CatalogPage

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=CatalogPage)
def list_catalog(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, max_length=100),
    category_id: int | None = Query(None, gt=0),
    size_id: int | None = Query(None, gt=0),
    color_id: int | None = Query(None, gt=0),
    branch_id: int | None = Query(None, gt=0),
    audience: str | None = Query(None, pattern="^(WOMEN|MEN|UNISEX)$"),
    season_id: int | None = Query(None, gt=0),
    collection_id: int | None = Query(None, gt=0),
    sort: str = Query("editorial", pattern="^(editorial|newest)$"),
):
    return service.list_catalog(db, page, page_size, q, category_id, size_id, color_id, branch_id, audience, season_id, collection_id, sort)


@router.get("/filters", response_model=CatalogFilters)
def get_catalog_filters(db: Session = Depends(get_db)):
    return service.catalog_filters(db)


@router.get("/navigation", response_model=CatalogNavigation)
def get_catalog_navigation(db: Session = Depends(get_db)):
    return service.catalog_navigation(db)


@router.get("/{product_id}", response_model=CatalogDetail)
def get_catalog_product(product_id: int, db: Session = Depends(get_db)):
    return service.serialize_detail(service.get_catalog_product(db, product_id))


@router.get("/{product_id}/availability", response_model=list[AvailabilityItem])
def get_availability(
    product_id: int,
    size_id: int = Query(..., gt=0),
    color_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    return service.availability(db, product_id, size_id, color_id)
