from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_branch_access, require_permission
from app.modules.reservations import service
from app.modules.reservations.schemas import ReservationCreateRequest, ReservationPage, ReservationResponse, ReservationStatusRequest


router = APIRouter(prefix="/reservations", tags=["reservations"])
ClientReservationUser = Annotated[User, Depends(require_permission("reservations.read"))]
BranchReservationUser = Annotated[User, Depends(require_permission("reservations.manage"))]


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(data: ReservationCreateRequest, current_user: ClientReservationUser, db=Depends(get_db)):
    reservation = service.create_reservation(db, data, current_user)
    db.commit()
    return service.serialize_reservation(reservation)


@router.get("/mine", response_model=ReservationPage)
def list_my_reservations(current_user: ClientReservationUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), reservation_status: str | None = Query(None, alias="status", max_length=30)):
    return service.list_reservations(db, page, page_size, customer_id=current_user.id, reservation_status=reservation_status)


@router.get("/branch", response_model=ReservationPage)
def list_branch_reservations(current_user: BranchReservationUser, db=Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), branch_id: int = Query(..., gt=0), reservation_status: str | None = Query(None, alias="status", max_length=30)):
    require_branch_access(current_user, branch_id)
    return service.list_reservations(db, page, page_size, branch_id=branch_id, reservation_status=reservation_status)


@router.get("/{reservation_id}", response_model=ReservationResponse)
def get_reservation(reservation_id: int, current_user: User = Depends(require_permission("reservations.read")), db=Depends(get_db)):
    reservation = service.get_reservation(db, reservation_id)
    if current_user.role.code != "ADMIN" and reservation.customer_id != current_user.id:
        require_branch_access(current_user, reservation.branch_id)
    return service.serialize_reservation(reservation)


@router.patch("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel_reservation(reservation_id: int, current_user: User = Depends(require_permission("reservations.read")), db=Depends(get_db)):
    reservation = service.get_reservation(db, reservation_id)
    if current_user.role.code != "ADMIN" and reservation.customer_id != current_user.id:
        require_branch_access(current_user, reservation.branch_id)
    result = service.change_status(db, reservation, ReservationStatusRequest(status="CANCELLED"), current_user)
    db.commit()
    return service.serialize_reservation(result)


@router.patch("/{reservation_id}/status", response_model=ReservationResponse)
def update_reservation_status(reservation_id: int, data: ReservationStatusRequest, current_user: BranchReservationUser, db=Depends(get_db)):
    reservation = service.get_reservation(db, reservation_id)
    require_branch_access(current_user, reservation.branch_id)
    result = service.change_status(db, reservation, data, current_user)
    db.commit()
    return service.serialize_reservation(result)
