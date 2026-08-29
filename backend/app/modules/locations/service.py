from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.models import Branch, City
from app.modules.locations.schemas import BranchCreateRequest, BranchUpdateRequest, CityCreateRequest, CityUpdateRequest


def _conflict(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"code": "LOCATION_CONFLICT", "message": message})


def serialize_city(city: City) -> dict[str, object]:
    return {"id": city.id, "name": city.name, "is_active": city.is_active}


def serialize_branch(branch: Branch) -> dict[str, object]:
    return {
        "id": branch.id,
        "city_id": branch.city_id,
        "city_name": branch.city.name,
        "name": branch.name,
        "address": branch.address,
        "phone": branch.phone,
        "latitude": branch.latitude,
        "longitude": branch.longitude,
        "is_active": branch.is_active,
    }


def list_cities(db: Session, page: int, page_size: int, query: str | None) -> dict[str, object]:
    statement = select(City).order_by(City.name)
    count_statement = select(func.count(City.id))
    if query:
        condition = City.name.ilike(f"%{query.strip()}%")
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_city(city) for city in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def get_city(db: Session, city_id: int) -> City:
    city = db.get(City, city_id)
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "CITY_NOT_FOUND", "message": "Ciudad no encontrada."})
    return city


def create_city(db: Session, data: CityCreateRequest) -> City:
    name = data.name.strip()
    if db.scalar(select(City.id).where(City.name == name)):
        raise _conflict("La ciudad ya está registrada.")
    city = City(name=name)
    db.add(city)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("La ciudad ya está registrada.") from exc
    return city


def update_city(db: Session, city: City, data: CityUpdateRequest) -> City:
    if data.name is not None:
        name = data.name.strip()
        existing = db.scalar(select(City.id).where(City.name == name, City.id != city.id))
        if existing:
            raise _conflict("La ciudad ya está registrada.")
        city.name = name
    db.flush()
    return city


def set_city_active(db: Session, city: City, active: bool) -> City:
    city.is_active = active
    db.flush()
    return city


def list_branches(db: Session, page: int, page_size: int, query: str | None, city_id: int | None) -> dict[str, object]:
    statement = select(Branch).options(joinedload(Branch.city)).order_by(Branch.name)
    count_statement = select(func.count(Branch.id))
    if query:
        condition = Branch.name.ilike(f"%{query.strip()}%")
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if city_id is not None:
        statement = statement.where(Branch.city_id == city_id)
        count_statement = count_statement.where(Branch.city_id == city_id)
    total = db.scalar(count_statement) or 0
    items = db.scalars(statement.offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [serialize_branch(branch) for branch in items], "page": page, "page_size": page_size, "total": total, "total_pages": ceil(total / page_size) if total else 0}


def get_branch(db: Session, branch_id: int) -> Branch:
    branch = db.scalar(select(Branch).options(joinedload(Branch.city)).where(Branch.id == branch_id))
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "BRANCH_NOT_FOUND", "message": "Sucursal no encontrada."})
    return branch


def _validate_city(db: Session, city_id: int) -> City:
    city = get_city(db, city_id)
    if not city.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"code": "CITY_INACTIVE", "message": "No se puede asociar una sucursal a una ciudad inactiva."})
    return city


def create_branch(db: Session, data: BranchCreateRequest) -> Branch:
    _validate_city(db, data.city_id)
    branch = Branch(**data.model_dump())
    db.add(branch)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("Ya existe una sucursal con ese nombre en la ciudad indicada.") from exc
    return get_branch(db, branch.id)


def update_branch(db: Session, branch: Branch, data: BranchUpdateRequest) -> Branch:
    values = data.model_dump(exclude_unset=True)
    if "city_id" in values:
        _validate_city(db, values["city_id"])
    for field, value in values.items():
        setattr(branch, field, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict("Ya existe una sucursal con ese nombre en la ciudad indicada.") from exc
    return get_branch(db, branch.id)


def set_branch_active(db: Session, branch: Branch, active: bool) -> Branch:
    branch.is_active = active
    db.flush()
    return get_branch(db, branch.id)
