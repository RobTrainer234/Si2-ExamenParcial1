from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_permission
from app.modules.seasons import service
from app.modules.seasons.schemas import CollectionCreateRequest, CollectionPage, CollectionResponse, CollectionUpdateRequest, SeasonCreateRequest, SeasonPage, SeasonResponse, SeasonUpdateRequest

router = APIRouter(tags=["seasons"])
AdminUser = Annotated[User, Depends(require_permission("seasons.manage"))]


@router.get("/seasons", response_model=SeasonPage)
def list_seasons(_: AdminUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = Query(None, max_length=100)):
    return service.list_seasons(db, page, page_size, q)


@router.post("/seasons", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
def create_season(data: SeasonCreateRequest, _: AdminUser, db=Depends(get_db)):
    season = service.create_season(db, data)
    db.commit()
    return service.serialize_season(season)


@router.get("/seasons/{season_id}", response_model=SeasonResponse)
def get_season(season_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_season(service.get_season(db, season_id))


@router.patch("/seasons/{season_id}", response_model=SeasonResponse)
def update_season(season_id: int, data: SeasonUpdateRequest, _: AdminUser, db=Depends(get_db)):
    season = service.update_season(db, service.get_season(db, season_id), data)
    db.commit()
    return service.serialize_season(season)


@router.patch("/seasons/{season_id}/{action}", response_model=SeasonResponse)
def season_status(season_id: int, action: str, _: AdminUser, db=Depends(get_db)):
    if action not in {"activate", "deactivate"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    season = service.set_season_active(db, service.get_season(db, season_id), action == "activate")
    db.commit()
    return service.serialize_season(season)


@router.get("/collections", response_model=CollectionPage)
def list_collections(_: AdminUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = Query(None, max_length=100), season_id: int | None = Query(None, gt=0)):
    return service.list_collections(db, page, page_size, q, season_id)


@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(data: CollectionCreateRequest, _: AdminUser, db=Depends(get_db)):
    collection = service.create_collection(db, data)
    db.commit()
    return service.serialize_collection(collection)


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
def get_collection(collection_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_collection(service.get_collection(db, collection_id))


@router.patch("/collections/{collection_id}", response_model=CollectionResponse)
def update_collection(collection_id: int, data: CollectionUpdateRequest, _: AdminUser, db=Depends(get_db)):
    collection = service.update_collection(db, service.get_collection(db, collection_id), data)
    db.commit()
    return service.serialize_collection(collection)


@router.patch("/collections/{collection_id}/{action}", response_model=CollectionResponse)
def collection_status(collection_id: int, action: str, _: AdminUser, db=Depends(get_db)):
    if action not in {"activate", "deactivate"}:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    collection = service.set_collection_active(db, service.get_collection(db, collection_id), action == "activate")
    db.commit()
    return service.serialize_collection(collection)
