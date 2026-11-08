from datetime import datetime
from typing import Any, Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from sqlalchemy import select

from app.core.database import get_db
from app.core.models import Branch, User
from app.modules.auth.dependencies import require_permission
from app.modules.reports import ai_service, export_service, ml_service, service
from app.modules.reports.schemas import (
    AudioTranscriptionRequest,
    AudioTranscriptionResponse,
    CustomerSegmentationResponse,
    DashboardResponse,
    DemandForecastResponse,
    LowStockItem,
    MLTrainingResponse,
    ReportAssistantRequest,
    ReportAssistantResponse,
    ReservationStatusItem,
    RevenueByCategoryItem,
    RevenueSummary,
    SalesByBranchItem,
    SalesByChannelItem,
    TopProductItem,
)
from app.modules.subscriptions.service import check_tenant_feature

router = APIRouter(prefix="/reports", tags=["reports"])
ReportsReader = Annotated[User, Depends(require_permission("reports.read"))]
ReportExportFormat = Literal["xlsx", "pdf", "pptx"]


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(_: ReportsReader, date_from: datetime | None = None, date_to: datetime | None = None, branch_id: int | None = None, db=Depends(get_db)):
    return service.dashboard(db, date_from, date_to, branch_id)


@router.post("/assistant", response_model=ReportAssistantResponse)
def report_assistant(current_user: ReportsReader, request: ReportAssistantRequest, db=Depends(get_db)):
    tenant_id = _require_ml_tenant(current_user)
    if not check_tenant_feature(db, tenant_id, "generative_reports_enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_NOT_IN_PLAN",
                "message": "Los reportes generativos con IA no están incluidos en su plan de suscripción.",
            },
        )
    return service.assistant_report(db, request, tenant_id=tenant_id)


def _require_ml_tenant(current_user: ReportsReader) -> int:
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "TENANT_CONTEXT_REQUIRED", "message": "A tenant context is required for ML reports."},
        )
    return current_user.tenant_id


def _validate_ml_parameter(name: str, value: int, minimum: int, maximum: int) -> None:
    if not minimum <= value <= maximum:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{name} must be between {minimum} and {maximum}.",
        )


def _require_active_tenant_branch(db, tenant_id: int, branch_id: int) -> None:
    branch = db.scalar(
        select(Branch).where(
            Branch.id == branch_id,
            Branch.tenant_id == tenant_id,
            Branch.is_active == True,  # noqa: E712
        )
    )
    if branch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")


def _label_report_field(field: object) -> str:
    labels = {
        "revenue": "Ingresos",
        "sales_count": "Cantidad de ventas",
        "total": "Total",
        "subtotal": "Subtotal",
        "discount": "Descuentos",
        "category_name": "Categoría",
        "product_name": "Producto",
        "branch_name": "Sucursal",
        "branch_id": "ID de sucursal",
        "product_id": "ID de producto",
        "inventory_id": "ID de inventario",
        "units_sold": "Unidades vendidas",
        "total_revenue": "Ingresos totales",
        "percentage": "Porcentaje",
        "available_quantity": "Stock disponible",
        "sku": "Código SKU",
        "status": "Estado",
        "count": "Cantidad",
        "channel": "Canal de venta",
    }
    return labels.get(str(field), str(field).replace("_", " ").capitalize())


def _normalize_report_data(data: Any) -> Any:
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if hasattr(data, "dict"):
        return data.dict()
    if isinstance(data, list):
        return [_normalize_report_data(item) for item in data]
    if isinstance(data, dict):
        return {key: _normalize_report_data(val) for key, val in data.items()}
    return data


def _assistant_export_rows(kind: str, data: Any, prompt: str) -> tuple[list[str], list[list[Any]]]:
    data = _normalize_report_data(data)
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        keys: list[str] = []
        for item in data:
            for key in item:
                if key not in keys:
                    keys.append(key)
        return [_label_report_field(key) for key in keys], [[item.get(key, "") for key in keys] for item in data]

    if isinstance(data, dict):
        rows: list[list[Any]] = []

        def add_values(section: str, value: Any) -> None:
            if isinstance(value, dict):
                for key, nested in value.items():
                    add_values(f"{section} · {_label_report_field(key)}", nested)
            elif isinstance(value, list):
                for index, item in enumerate(value, start=1):
                    add_values(f"{section} · Registro {index}", item)
            else:
                rows.append([section, value])

        for key, value in data.items():
            add_values(_label_report_field(key), value)
        rows.append(["Consulta", prompt])
        return ["Sección", "Dato"], rows

    if isinstance(data, list):
        return ["Índice", "Valor"], [[index, value] for index, value in enumerate(data, start=1)]

    return ["Campo", "Valor"], [["Resultado", data], ["Consulta", prompt]]


@router.post("/assistant/export/{format_name}")
def export_assistant_report(
    current_user: ReportsReader,
    format_name: Literal["xlsx", "pdf"],
    request: ReportAssistantRequest,
    db=Depends(get_db),
):
    tenant_id = _require_ml_tenant(current_user)
    if not check_tenant_feature(db, tenant_id, "generative_reports_enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_NOT_IN_PLAN",
                "message": "Los reportes generativos con IA no están incluidos en su plan de suscripción.",
            },
        )
    rep_res = service.assistant_report(db, request, tenant_id=tenant_id)

    title = f"Reporte: {rep_res.intent.kind.replace('_', ' ').title()}"
    headers, rows = _assistant_export_rows(rep_res.intent.kind, rep_res.data, request.prompt)

    exported = export_service.export_dynamic_report(
        title=title,
        headers=headers,
        rows=rows,
        narrative=rep_res.narrative,
        format_name=format_name,
    )
    return Response(
        content=exported.content,
        media_type=exported.media_type,
        headers={"Content-Disposition": f'attachment; filename="{exported.filename}"'},
    )


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


@router.get("/revenue-by-category", response_model=list[RevenueByCategoryItem])
def revenue_by_category(
    _: ReportsReader,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    branch_id: int | None = None,
    db=Depends(get_db),
):
    return service.revenue_by_category(db, date_from, date_to, branch_id)


@router.get("/ml/demand-forecast", response_model=DemandForecastResponse)
def demand_forecast(
    current_user: ReportsReader,
    branch_id: int | None = None,
    weeks_ahead: int = Query(6, ge=1, le=12),
    db=Depends(get_db),
):
    tenant_id = _require_ml_tenant(current_user)
    _validate_ml_parameter("weeks_ahead", weeks_ahead, 1, 12)
    if branch_id is not None:
        _require_active_tenant_branch(db, tenant_id, branch_id)
    if not check_tenant_feature(db, tenant_id, "generative_reports_enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_NOT_IN_PLAN",
                "message": "Los modelos predictivos y reportes con IA no están incluidos en su plan de suscripción.",
            },
        )
    return ml_service.DemandForecastService.forecast_demand(db, tenant_id=tenant_id, branch_id=branch_id, weeks_ahead=weeks_ahead)


@router.get("/ml/customer-segments", response_model=CustomerSegmentationResponse)
def customer_segments(
    current_user: ReportsReader,
    n_clusters: int = Query(4, ge=2, le=12),
    db=Depends(get_db),
):
    tenant_id = _require_ml_tenant(current_user)
    _validate_ml_parameter("n_clusters", n_clusters, 2, 12)
    if not check_tenant_feature(db, tenant_id, "generative_reports_enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_NOT_IN_PLAN",
                "message": "La segmentación analítica no supervisada no está incluida en su plan de suscripción.",
            },
        )
    return ml_service.CustomerSegmentationService.segment_customers(db, tenant_id=tenant_id, n_clusters=n_clusters)


@router.post("/ml/train", response_model=MLTrainingResponse)
def train_ml_models(
    current_user: ReportsReader,
    db=Depends(get_db),
):
    tenant_id = _require_ml_tenant(current_user)
    if not check_tenant_feature(db, tenant_id, "generative_reports_enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_NOT_IN_PLAN",
                "message": "El entrenamiento de modelos analíticos no está incluido en su plan de suscripción.",
            },
        )
    return ml_service.CustomerSegmentationService.retrain_models(db, tenant_id=tenant_id)


@router.post("/transcribe-audio", response_model=AudioTranscriptionResponse)
def transcribe_audio(
    current_user: ReportsReader,
    request: AudioTranscriptionRequest,
    db=Depends(get_db),
):
    if current_user.tenant_id is not None and not check_tenant_feature(db, current_user.tenant_id, "generative_reports_enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_NOT_IN_PLAN",
                "message": "Los reportes generativos con IA no están incluidos en su plan de suscripción.",
            },
        )
    try:
        transcript = ai_service.transcribe_audio_prompt(request.audio_base64, request.mime_type)
    except Exception:
        transcript = None
    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "TRANSCRIPTION_UNAVAILABLE",
                "message": "La transcripción no está disponible en este momento.",
            },
        )
    return AudioTranscriptionResponse(text=transcript.strip())


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
