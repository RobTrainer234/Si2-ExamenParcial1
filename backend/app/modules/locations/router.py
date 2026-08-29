from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_admin
from app.modules.locations import service
from app.modules.locations.schemas import BranchCreateRequest, BranchPage, BranchResponse, BranchUpdateRequest, CityCreateRequest, CityPage, CityResponse, CityUpdateRequest

router = APIRouter(tags=["locations"])
AdminUser = Annotated[User, Depends(require_admin)]


@router.get("/cities", response_model=CityPage)
def list_cities(
    _: AdminUser,
    db=Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=100),
):
    return service.list_cities(db, page, page_size, q)


@router.post("/cities", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
def create_city(data: CityCreateRequest, _: AdminUser, db=Depends(get_db)):
    city = service.create_city(db, data)
    db.commit()
    return service.serialize_city(city)


@router.get("/cities/{city_id}", response_model=CityResponse)
def get_city(city_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_city(service.get_city(db, city_id))


@router.patch("/cities/{city_id}", response_model=CityResponse)
def update_city(city_id: int, data: CityUpdateRequest, _: AdminUser, db=Depends(get_db)):
    city = service.update_city(db, service.get_city(db, city_id), data)
    db.commit()
    return service.serialize_city(city)


@router.patch("/cities/{city_id}/activate", response_model=CityResponse)
def activate_city(city_id: int, _: AdminUser, db=Depends(get_db)):
    city = service.set_city_active(db, service.get_city(db, city_id), True)
    db.commit()
    return service.serialize_city(city)


@router.patch("/cities/{city_id}/deactivate", response_model=CityResponse)
def deactivate_city(city_id: int, _: AdminUser, db=Depends(get_db)):
    city = service.set_city_active(db, service.get_city(db, city_id), False)
    db.commit()
    return service.serialize_city(city)


@router.get("/branches", response_model=BranchPage)
def list_branches(
    _: AdminUser,
    db=Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=100),
    city_id: int | None = Query(default=None, gt=0),
):
    return service.list_branches(db, page, page_size, q, city_id)


@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
def create_branch(data: BranchCreateRequest, _: AdminUser, db=Depends(get_db)):
    branch = service.create_branch(db, data)
    db.commit()
    return service.serialize_branch(branch)


@router.get("/branches/{branch_id}", response_model=BranchResponse)
def get_branch(branch_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_branch(service.get_branch(db, branch_id))


@router.patch("/branches/{branch_id}", response_model=BranchResponse)
def update_branch(branch_id: int, data: BranchUpdateRequest, _: AdminUser, db=Depends(get_db)):
    branch = service.update_branch(db, service.get_branch(db, branch_id), data)
    db.commit()
    return service.serialize_branch(branch)


@router.patch("/branches/{branch_id}/activate", response_model=BranchResponse)
def activate_branch(branch_id: int, _: AdminUser, db=Depends(get_db)):
    branch = service.set_branch_active(db, service.get_branch(db, branch_id), True)
    db.commit()
    return service.serialize_branch(branch)


@router.patch("/branches/{branch_id}/deactivate", response_model=BranchResponse)
def deactivate_branch(branch_id: int, _: AdminUser, db=Depends(get_db)):
    branch = service.set_branch_active(db, service.get_branch(db, branch_id), False)
    db.commit()
    return service.serialize_branch(branch)
