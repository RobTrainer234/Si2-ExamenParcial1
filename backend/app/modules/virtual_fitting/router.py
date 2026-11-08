from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import bind_optional_tenant_context, require_permission
from app.modules.virtual_fitting import service
from app.modules.virtual_fitting.schemas import (
    VirtualFittingListResponse,
    VirtualFittingSessionResponse,
    VirtualFittingStartRequest,
    VtonTryOnRequest,
    VtonTryOnResponse,
)
from app.modules.virtual_fitting.vton_service import VtonService

router = APIRouter(prefix="/virtual-fitting", tags=["virtual-fitting"])
VirtualFittingClient = Annotated[User, Depends(require_permission("virtual_fitting.use"))]


@router.post("/sessions", response_model=VirtualFittingSessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(data: VirtualFittingStartRequest, current_user: VirtualFittingClient, db=Depends(get_db)):
    item = service.start_session(db, data, current_user)
    db.commit()
    return service.serialize(item)


@router.patch("/sessions/{session_id}/finish", response_model=VirtualFittingSessionResponse)
def finish_session(session_id: int, current_user: VirtualFittingClient, db=Depends(get_db)):
    item = service.finish_session(db, session_id, current_user)
    db.commit()
    return service.serialize(item)


@router.get("/sessions/mine", response_model=VirtualFittingListResponse)
def list_mine(current_user: VirtualFittingClient, db=Depends(get_db)):
    return {"items": [service.serialize(item) for item in service.list_mine(db, current_user)]}


@router.post("/vton/try-on", response_model=VtonTryOnResponse)
def vton_try_on(data: VtonTryOnRequest, current_user: VirtualFittingClient, db=Depends(get_db)):
    return VtonService.process_try_on(
        db=db,
        product_id=data.product_id,
        user=current_user,
        image_base64=data.image_base64,
        metrics=data.metrics,
    )


catalogo_vton_router = APIRouter(prefix="/catalogo", tags=["catalogo"], dependencies=[Depends(bind_optional_tenant_context)])


@catalogo_vton_router.post("/vton/try-on", response_model=VtonTryOnResponse)
def catalogo_vton_try_on(data: VtonTryOnRequest, db=Depends(get_db)):
    return VtonService.process_try_on(
        db=db,
        product_id=data.product_id,
        image_base64=data.image_base64,
        metrics=data.metrics,
    )


