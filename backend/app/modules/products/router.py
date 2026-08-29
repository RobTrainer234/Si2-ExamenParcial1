from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_admin
from app.modules.products import service
from app.modules.products.schemas import ImageInput, ProductCreateRequest, ProductPage, ProductResponse, ProductUpdateRequest, VariantInput

router = APIRouter(prefix="/products", tags=["products"])
AdminUser = Annotated[User, Depends(require_admin)]


@router.get("", response_model=ProductPage)
def list_products(_: AdminUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = Query(None, max_length=100), category_id: int | None = Query(None, gt=0)):
    return service.list_products(db, page, page_size, q, category_id)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreateRequest, _: AdminUser, db=Depends(get_db)):
    product = service.create_product(db, data)
    db.commit()
    return service.serialize_product(product)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_product(service.get_product(db, product_id))


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdateRequest, _: AdminUser, db=Depends(get_db)):
    product = service.update_product(db, service.get_product(db, product_id), data)
    db.commit()
    return service.serialize_product(product)


@router.patch("/{product_id}/activate", response_model=ProductResponse)
def activate_product(product_id: int, _: AdminUser, db=Depends(get_db)):
    product = service.set_product_active(db, service.get_product(db, product_id), True)
    db.commit()
    return service.serialize_product(product)


@router.patch("/{product_id}/deactivate", response_model=ProductResponse)
def deactivate_product(product_id: int, _: AdminUser, db=Depends(get_db)):
    product = service.set_product_active(db, service.get_product(db, product_id), False)
    db.commit()
    return service.serialize_product(product)


@router.post("/{product_id}/variants", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def add_variant(product_id: int, data: VariantInput, _: AdminUser, db=Depends(get_db)):
    product = service.add_variant(db, service.get_product(db, product_id), data)
    db.commit()
    return service.serialize_product(product)


@router.post("/{product_id}/images", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def add_image(product_id: int, data: ImageInput, _: AdminUser, db=Depends(get_db)):
    product = service.add_image(db, service.get_product(db, product_id), data)
    db.commit()
    return service.serialize_product(product)
