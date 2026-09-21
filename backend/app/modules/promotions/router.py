from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_permission
from app.modules.promotions import service
from app.modules.promotions.schemas import PromotionCreate, PromotionPage, PromotionProductsRequest, PromotionResponse, PromotionUpdate

router = APIRouter(prefix="/promotions", tags=["promotions"])
PromotionManager = Annotated[User, Depends(require_permission("promotions.manage"))]


@router.get("", response_model=PromotionPage)
def list_promotions(_: PromotionManager, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), q: str | None = None, db=Depends(get_db)):
    return service.list_promotions(db, page, page_size, q)


@router.post("", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
def create_promotion(data: PromotionCreate, current_user: PromotionManager, db=Depends(get_db)):
    item = service.create_promotion(db, data, current_user)
    db.commit()
    return service.serialize(item)


@router.get("/{promotion_id}", response_model=PromotionResponse)
def get_promotion(promotion_id: int, _: PromotionManager, db=Depends(get_db)):
    return service.serialize(service.get_promotion(db, promotion_id))


@router.patch("/{promotion_id}", response_model=PromotionResponse)
def update_promotion(promotion_id: int, data: PromotionUpdate, current_user: PromotionManager, db=Depends(get_db)):
    item = service.update_promotion(db, promotion_id, data, current_user)
    db.commit()
    return service.serialize(item)


@router.patch("/{promotion_id}/activate", response_model=PromotionResponse)
def activate_promotion(promotion_id: int, current_user: PromotionManager, db=Depends(get_db)):
    item = service.set_status(db, promotion_id, True, current_user)
    db.commit()
    return service.serialize(item)


@router.patch("/{promotion_id}/deactivate", response_model=PromotionResponse)
def deactivate_promotion(promotion_id: int, current_user: PromotionManager, db=Depends(get_db)):
    item = service.set_status(db, promotion_id, False, current_user)
    db.commit()
    return service.serialize(item)


@router.post("/{promotion_id}/products", response_model=PromotionResponse)
def set_promotion_products(promotion_id: int, data: PromotionProductsRequest, current_user: PromotionManager, db=Depends(get_db)):
    item = service.set_products(db, promotion_id, data.product_ids, current_user)
    db.commit()
    return service.serialize(item)
