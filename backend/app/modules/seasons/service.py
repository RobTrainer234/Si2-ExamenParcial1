from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.models import Collection, Season
from app.modules.seasons.schemas import CollectionCreateRequest, CollectionUpdateRequest, SeasonCreateRequest, SeasonUpdateRequest


def _conflict(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "SEASON_CONFLICT", "message": message})


def _not_found(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": code, "message": message})


def get_season(db: Session, season_id: int) -> Season:
    season = db.get(Season, season_id)
    if season is None:
        raise _not_found("SEASON_NOT_FOUND", "Temporada no encontrada.")
    return season


def get_collection(db: Session, collection_id: int) -> Collection:
    collection = db.scalar(select(Collection).options(joinedload(Collection.season)).where(Collection.id == collection_id))
    if collection is None:
        raise _not_found("COLLECTION_NOT_FOUND", "Colección no encontrada.")
    return collection


def serialize_season(season: Season) -> dict[str, object]:
    return {"id": season.id, "name": season.name, "starts_on": season.starts_on, "ends_on": season.ends_on, "is_active": season.is_active}


def serialize_collection(collection: Collection) -> dict[str, object]:
    return {"id": collection.id, "season_id": collection.season_id, "season_name": collection.season.name, "name": collection.name, "description": collection.description, "is_active": collection.is_active}


def list_seasons(db: Session, page: int, page_size: int, query: str | None) -> dict[str, object]:
    statement = select(Season).order_by(Season.name)
    count_statement = select(func.count(Season.id))
    if query:
        condition = Season.name.ilike(f"%{query.strip()}%")
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_season(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def create_season(db: Session, data: SeasonCreateRequest) -> Season:
    if db.scalar(select(Season.id).where(Season.name == data.name)):
        raise _conflict("La temporada ya está registrada.")
    season = Season(**data.model_dump())
    db.add(season)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("La temporada ya está registrada.") from exc
    return season


def update_season(db: Session, season: Season, data: SeasonUpdateRequest) -> Season:
    values = data.model_dump(exclude_unset=True)
    if values.get("name") and db.scalar(select(Season.id).where(Season.name == values["name"], Season.id != season.id)):
        raise _conflict("La temporada ya está registrada.")
    for field, value in values.items():
        setattr(season, field, value)
    db.flush()
    return season


def set_season_active(db: Session, season: Season, active: bool) -> Season:
    season.is_active = active
    db.flush()
    return season


def _active_season(db: Session, season_id: int) -> Season:
    season = get_season(db, season_id)
    if not season.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "SEASON_INACTIVE", "message": "La temporada está inactiva."})
    return season


def list_collections(db: Session, page: int, page_size: int, query: str | None, season_id: int | None) -> dict[str, object]:
    statement = select(Collection).options(joinedload(Collection.season)).order_by(Collection.name)
    count_statement = select(func.count(Collection.id))
    if query:
        condition = Collection.name.ilike(f"%{query.strip()}%")
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if season_id is not None:
        statement = statement.where(Collection.season_id == season_id)
        count_statement = count_statement.where(Collection.season_id == season_id)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_collection(item) for item in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def create_collection(db: Session, data: CollectionCreateRequest) -> Collection:
    _active_season(db, data.season_id)
    if db.scalar(select(Collection.id).where(Collection.season_id == data.season_id, Collection.name == data.name)):
        raise _conflict("La colección ya está registrada para esa temporada.")
    collection = Collection(**data.model_dump())
    db.add(collection)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("La colección ya está registrada para esa temporada.") from exc
    return get_collection(db, collection.id)


def update_collection(db: Session, collection: Collection, data: CollectionUpdateRequest) -> Collection:
    values = data.model_dump(exclude_unset=True)
    target_season_id = values.get("season_id", collection.season_id)
    _active_season(db, target_season_id)
    if values.get("name") and db.scalar(select(Collection.id).where(Collection.season_id == target_season_id, Collection.name == values["name"], Collection.id != collection.id)):
        raise _conflict("La colección ya está registrada para esa temporada.")
    for field, value in values.items():
        setattr(collection, field, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("La colección ya está registrada para esa temporada.") from exc
    return get_collection(db, collection.id)


def set_collection_active(db: Session, collection: Collection, active: bool) -> Collection:
    collection.is_active = active
    db.flush()
    return get_collection(db, collection.id)
