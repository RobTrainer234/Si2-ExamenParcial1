from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_permission
from app.modules.reports import export_service, service
from app.modules.reports.schemas import DashboardResponse, LowStockItem, ReportAssistantRequest, ReportAssistantResponse, ReservationStatusItem, RevenueSummary, SalesByBranchItem, SalesByChannelItem, TopProductItem

router = APIRouter(prefix="/reports", tags=["reports"])
ReportsReader = Annotated[User, Depends(require_permission("reports.read"))]
ReportExportFormat = Literal["xlsx", "pdf", "pptx"]


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(_: ReportsReader, date_from: datetime | None = None, date_to: datetime | None = None, branch_id: int | None = None, db=Depends(get_db)):
    return service.dashboard(db, date_from, date_to, branch_id)


@router.post("/assistant", response_model=ReportAssistantResponse)
def report_assistant(_: ReportsReader, request: ReportAssistantRequest, db=Depends(get_db)):
    return service.assistant_report(db, request)


@router.get("/sales-by-branch", response_model=list[SalesByBranchItem])
def sales_by_branch(_: ReportsReader, date_from: datetime | None = None, date_to: datetime | None = None, branch_id: int | None = None, db=Depends(get_db)):
    return service.sales_by_branch(db, date_from, date_to, branch_id)


@router.get("/top-products", response_model=list[TopProductItem])
def top_products(_: ReportsReader, date_from: datetime | None = None, date_to: datetime | None = None, branch_id: int | None = None, db=Depends(get_db)):
    return service.top_products(db, date_from, date_to, branch_id)


@router.get("/low-stock", response_model=list[LowStockItem])
def low_stock(_: ReportsReader, branch_id: int | None = None, threshold: int = 10, db=Depends(get_db)):
    return service.low_stock(db, branch_id, threshold)


@router.get("/reservations-summary", response_model=list[ReservationStatusItem])
def reservations_summary(_: ReportsReader, branch_id: int | None = None, db=Depends(get_db)):
    return service.reservations_summary(db, branch_id)


@router.get("/sales-by-channel", response_model=list[SalesByChannelItem])
def sales_by_channel(_: ReportsReader, date_from: datetime | None = None, date_to: datetime | None = None, branch_id: int | None = None, db=Depends(get_db)):
    return service.sales_by_channel(db, date_from, date_to, branch_id)


@router.get("/revenue-summary", response_model=RevenueSummary)
def revenue_summary(_: ReportsReader, date_from: datetime | None = None, date_to: datetime | None = None, branch_id: int | None = None, db=Depends(get_db)):
    return service.revenue_summary(db, date_from, date_to, branch_id)


@router.get("/export/{format_name}")
def export_report(
    _: ReportsReader,
    format_name: ReportExportFormat,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: int | None = None,
    db=Depends(get_db),
):
    snapshot = service.report_snapshot(db, date_from, date_to, branch_id)
    exported = export_service.export_snapshot(snapshot, format_name)
    return Response(
        content=exported.content,
        media_type=exported.media_type,
        headers={"Content-Disposition": f'attachment; filename="{exported.filename}"'},
    )
