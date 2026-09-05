from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.core.config import settings
from app.core.audit import record_audit
from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_permission
from app.modules.products import service
from app.modules.products.schemas import ImageInput, ImageUpdateRequest, ProductCreateRequest, ProductPage, ProductResponse, ProductUpdateRequest, VariantBatchInput, VariantInput

router = APIRouter(prefix="/products", tags=["products"])
AdminUser = Annotated[User, Depends(require_permission("products.manage"))]


@router.get("", response_model=ProductPage)
def list_products(_: AdminUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = Query(None, max_length=100), category_id: int | None = Query(None, gt=0)):
    return service.list_products(db, page, page_size, q, category_id)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreateRequest, current_user: AdminUser, db=Depends(get_db)):
    product = service.create_product(db, data)
    record_audit(db, current_user, "CREATE", "product", product.id, "Producto creado.", new_values={"code": product.code, "name": product.name})
    db.commit()
    return service.serialize_product(product)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, _: AdminUser, db=Depends(get_db)):
    return service.serialize_product(service.get_product(db, product_id))


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, data: ProductUpdateRequest, current_user: AdminUser, db=Depends(get_db)):
    product = service.get_product(db, product_id)
    old_values = {field: getattr(product, field) for field in data.model_dump(exclude_unset=True)}
    product = service.update_product(db, product, data)
    record_audit(db, current_user, "UPDATE", "product", product.id, "Producto actualizado.", old_values=old_values, new_values=data.model_dump(exclude_unset=True))
    db.commit()
    return service.serialize_product(product)


@router.patch("/{product_id}/activate", response_model=ProductResponse)
def activate_product(product_id: int, current_user: AdminUser, db=Depends(get_db)):
    product = service.set_product_active(db, service.get_product(db, product_id), True)
    record_audit(db, current_user, "UPDATE", "product", product.id, "Producto activado.", new_values={"is_active": True})
    db.commit()
    return service.serialize_product(product)


@router.patch("/{product_id}/deactivate", response_model=ProductResponse)
def deactivate_product(product_id: int, current_user: AdminUser, db=Depends(get_db)):
    product = service.set_product_active(db, service.get_product(db, product_id), False)
    record_audit(db, current_user, "UPDATE", "product", product.id, "Producto desactivado.", new_values={"is_active": False})
    db.commit()
    return service.serialize_product(product)


@router.post("/{product_id}/variants", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def add_variant(product_id: int, data: VariantInput, _: AdminUser, db=Depends(get_db)):
    product = service.add_variant(db, service.get_product(db, product_id), data)
    db.commit()
    return service.serialize_product(product)


@router.post("/{product_id}/variants/bulk", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def add_variants_bulk(product_id: int, data: VariantBatchInput, _: AdminUser, db=Depends(get_db)):
    product = service.add_variants_bulk(db, service.get_product(db, product_id), data.variants)
    db.commit()
    return service.serialize_product(product)


@router.post("/{product_id}/images", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def add_image(product_id: int, data: ImageInput, _: AdminUser, db=Depends(get_db)):
    product = service.add_image(db, service.get_product(db, product_id), data)
    db.commit()
    return service.serialize_product(product)


@router.post("/{product_id}/images/upload", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(product_id: int, admin: AdminUser, file: UploadFile = File(...), is_primary: bool = Form(False), sort_order: int = Form(0), db=Depends(get_db)):
    del admin
    product = service.get_product(db, product_id)
    data = await file.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail={"code": "IMAGE_TOO_LARGE", "message": "La imagen no puede superar los 5 MB."})
    media_root = Path(settings.media_dir) / "products"
    image_url, destination = service.uploaded_image_name(file.content_type, data, media_root)
    try:
        product = service.add_uploaded_image(db, product, image_url, is_primary, sort_order)
        db.commit()
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return service.serialize_product(product)


@router.patch("/{product_id}/images/{image_id}", response_model=ProductResponse)
def update_image(product_id: int, image_id: int, data: ImageUpdateRequest, _: AdminUser, db=Depends(get_db)):
    product = service.update_image(db, service.get_product(db, product_id), image_id, data.is_primary, data.sort_order)
    db.commit()
    return service.serialize_product(product)


@router.delete("/{product_id}/images/{image_id}", response_model=ProductResponse)
def delete_image(product_id: int, image_id: int, _: AdminUser, db=Depends(get_db)):
    product, image_url = service.delete_image(db, service.get_product(db, product_id), image_id)
    db.commit()
    if image_url and image_url.startswith("/media/"):
        Path(settings.media_dir, image_url.removeprefix("/media/")).unlink(missing_ok=True)
    return service.serialize_product(product)
