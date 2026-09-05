from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_db
from app.core.models import Category, Color, Size, User
from app.modules.auth.dependencies import require_permission
from app.modules.catalog_masters import service
from app.modules.catalog_masters.schemas import CategoryCreateRequest, CategoryResponse, CategoryUpdateRequest, ColorCreateRequest, ColorResponse, ColorUpdateRequest, MasterPage, SizeCreateRequest, SizeResponse, SizeUpdateRequest

router = APIRouter(tags=["catalog-masters"])
AdminUser = Annotated[User, Depends(require_permission("masters.manage"))]


def _list(model: type[Any], _: AdminUser, db: Any, page: int, page_size: int, q: str | None):
    return service.list_master(db, model, page, page_size, q)


@router.get("/categories", response_model=MasterPage[CategoryResponse])
def list_categories(_: AdminUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = Query(None, max_length=100)):
    return _list(Category, _, db, page, page_size, q)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreateRequest, _: AdminUser, db=Depends(get_db)):
    item = service.create_master(db, Category, data.model_dump(), "Categoría")
    db.commit()
    return service.serialize_master(item)


@router.get("/categories/{item_id}", response_model=CategoryResponse)
def get_category(item_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_master(service.get_master(db, Category, item_id, "CATEGORY_NOT_FOUND", "Categoría"))


@router.patch("/categories/{item_id}", response_model=CategoryResponse)
def update_category(item_id: int, data: CategoryUpdateRequest, _: AdminUser, db=Depends(get_db)):
    item = service.update_master(db, service.get_master(db, Category, item_id, "CATEGORY_NOT_FOUND", "Categoría"), data.model_dump(exclude_unset=True), "Categoría")
    db.commit()
    return service.serialize_master(item)


@router.patch("/categories/{item_id}/{action}", response_model=CategoryResponse)
def category_status(item_id: int, action: str, _: AdminUser, db=Depends(get_db)):
    item = service.get_master(db, Category, item_id, "CATEGORY_NOT_FOUND", "Categoría")
    if action not in {"activate", "deactivate"}:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    item = service.set_active(db, item, action == "activate")
    db.commit()
    return service.serialize_master(item)


@router.get("/sizes", response_model=MasterPage[SizeResponse])
def list_sizes(_: AdminUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = Query(None, max_length=100)):
    return _list(Size, _, db, page, page_size, q)


@router.post("/sizes", response_model=SizeResponse, status_code=status.HTTP_201_CREATED)
def create_size(data: SizeCreateRequest, _: AdminUser, db=Depends(get_db)):
    item = service.create_master(db, Size, data.model_dump(), "Talla")
    db.commit()
    return service.serialize_master(item)


@router.get("/sizes/{item_id}", response_model=SizeResponse)
def get_size(item_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_master(service.get_master(db, Size, item_id, "SIZE_NOT_FOUND", "Talla"))


@router.patch("/sizes/{item_id}", response_model=SizeResponse)
def update_size(item_id: int, data: SizeUpdateRequest, _: AdminUser, db=Depends(get_db)):
    item = service.update_master(db, service.get_master(db, Size, item_id, "SIZE_NOT_FOUND", "Talla"), data.model_dump(exclude_unset=True), "Talla")
    db.commit()
    return service.serialize_master(item)


@router.patch("/sizes/{item_id}/{action}", response_model=SizeResponse)
def size_status(item_id: int, action: str, _: AdminUser, db=Depends(get_db)):
    item = service.get_master(db, Size, item_id, "SIZE_NOT_FOUND", "Talla")
    if action not in {"activate", "deactivate"}:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    item = service.set_active(db, item, action == "activate")
    db.commit()
    return service.serialize_master(item)


@router.get("/colors", response_model=MasterPage[ColorResponse])
def list_colors(_: AdminUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = Query(None, max_length=100)):
    return _list(Color, _, db, page, page_size, q)


@router.post("/colors", response_model=ColorResponse, status_code=status.HTTP_201_CREATED)
def create_color(data: ColorCreateRequest, _: AdminUser, db=Depends(get_db)):
    item = service.create_master(db, Color, data.model_dump(), "Color")
    db.commit()
    return service.serialize_master(item)


@router.get("/colors/{item_id}", response_model=ColorResponse)
def get_color(item_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_master(service.get_master(db, Color, item_id, "COLOR_NOT_FOUND", "Color"))


@router.patch("/colors/{item_id}", response_model=ColorResponse)
def update_color(item_id: int, data: ColorUpdateRequest, _: AdminUser, db=Depends(get_db)):
    item = service.update_master(db, service.get_master(db, Color, item_id, "COLOR_NOT_FOUND", "Color"), data.model_dump(exclude_unset=True), "Color")
    db.commit()
    return service.serialize_master(item)


@router.patch("/colors/{item_id}/{action}", response_model=ColorResponse)
def color_status(item_id: int, action: str, _: AdminUser, db=Depends(get_db)):
    item = service.get_master(db, Color, item_id, "COLOR_NOT_FOUND", "Color")
    if action not in {"activate", "deactivate"}:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    item = service.set_active(db, item, action == "activate")
    db.commit()
    return service.serialize_master(item)
