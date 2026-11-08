from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_permission
from app.modules.sync import service
from app.modules.sync.schemas import (
    SyncCatalogResponse,
    SyncTransactionBatchRequest,
    SyncTransactionBatchResponse,
    SyncTransactionItemResult,
)

router = APIRouter(prefix="/sync", tags=["sync"])
CatalogSyncUser = Annotated[User, Depends(require_permission("catalog.read"))]


@router.get("/catalog", response_model=SyncCatalogResponse)
def sync_catalog(
    current_user: CatalogSyncUser,
    branch_id: int | None = Query(default=None, gt=0),
    since: datetime | None = Query(default=None),
    db=Depends(get_db),
):
    return service.get_sync_catalog(db, current_user, branch_id=branch_id, since=since)


@router.post("/transactions", response_model=SyncTransactionBatchResponse)
def sync_transactions(
    current_user: CatalogSyncUser,
    batch: SyncTransactionBatchRequest,
    db=Depends(get_db),
):
    return service.process_sync_transactions_batch(db, current_user, batch)


@router.get("/transactions/{client_operation_id}", response_model=SyncTransactionItemResult)
def get_transaction_status(
    client_operation_id: str,
    current_user: CatalogSyncUser,
    db=Depends(get_db),
):
    return service.get_sync_transaction_status(db, current_user, client_operation_id)

