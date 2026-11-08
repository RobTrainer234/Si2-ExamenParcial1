import base64
import binascii
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SalesByBranchItem(BaseModel):
    branch_id: int | None
    branch_name: str
    sales_count: int
    total: Decimal


class TopProductItem(BaseModel):
    product_id: int
    product_name: str
    units_sold: int
    revenue: Decimal


class LowStockItem(BaseModel):
    inventory_id: int
    branch_id: int
    branch_name: str
    product_id: int
    product_name: str
    sku: str
    available_quantity: int


class ReservationStatusItem(BaseModel):
    status: str
    count: int


class SalesByChannelItem(BaseModel):
    channel: str
    sales_count: int
    total: Decimal


class RevenueSummary(BaseModel):
    sales_count: int
    subtotal: Decimal
    discount: Decimal
    total: Decimal


class DashboardResponse(BaseModel):
    revenue: RevenueSummary
    sales_by_branch: list[SalesByBranchItem]
    top_products: list[TopProductItem]
    low_stock: list[LowStockItem]
    reservations: list[ReservationStatusItem]
    sales_by_channel: list[SalesByChannelItem]


class ReportFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date_from: datetime | None = None
    date_to: datetime | None = None
    branch_id: int | None = None


class RevenueByCategoryItem(BaseModel):
    category_id: int
    category_name: str
    sales_count: int
    units_sold: int
    total_revenue: Decimal
    percentage: float


class ReportSnapshot(DashboardResponse):
    filters: ReportFilters


ReportAssistantIntentKind = Literal[
    "dashboard",
    "top_products",
    "sales_by_branch",
    "inventory",
    "reservations",
    "revenue_by_category",
]
ReportAssistantProvider = Literal["gemini", "openai", "local"]
ChartType = Literal["bar", "line", "pie", "table", "kpi"]


class ReportAssistantRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=1000)
    date_from: datetime | None = None
    date_to: datetime | None = None
    branch_id: int | None = None


class ReportAssistantIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ReportAssistantIntentKind
    filters: ReportFilters = Field(default_factory=ReportFilters)
    chart_type: ChartType = "bar"
    reasoning: str = ""


class ReportAssistantResponse(BaseModel):
    intent: ReportAssistantIntent
    filters: ReportFilters
    data: (
        DashboardResponse
        | list[TopProductItem]
        | list[SalesByBranchItem]
        | list[LowStockItem]
        | list[ReservationStatusItem]
        | list[RevenueByCategoryItem]
    )
    narrative: str
    chart_type: ChartType = "bar"
    provider: ReportAssistantProvider
    fallback_used: bool


# --------------------------------------------------------------------------
# Schemas para Analítica Inteligente con Machine Learning (Sección 8.4)
# --------------------------------------------------------------------------

class MLModelMetrics(BaseModel):
    model_name: str
    model_type: Literal["supervised", "unsupervised"]
    mae: float | None = None
    rmse: float | None = None
    r2_score: float | None = None
    silhouette_score: float | None = None
    inertia: float | None = None
    samples_count: int
    real_samples_count: int | None = None
    synthetic_samples_count: int | None = None
    trained_at: datetime


class DemandForecastPoint(BaseModel):
    period: str
    predicted_units: int
    predicted_revenue: Decimal
    confidence_lower: Decimal
    confidence_upper: Decimal


class DemandForecastResponse(BaseModel):
    target: str = "ventas_semanales"
    branch_id: int | None = None
    branch_name: str | None = None
    forecast: list[DemandForecastPoint]
    metrics: MLModelMetrics
    narrative: str


class CustomerSegmentItem(BaseModel):
    segment_id: int
    name: str
    description: str
    customer_count: int
    percentage: float
    avg_recency_days: float
    avg_frequency: float
    avg_monetary: Decimal
    suggested_action: str


class CustomerAnomalyItem(BaseModel):
    recency_days: float
    frequency: float
    monetary: Decimal
    anomaly_score: float
    data_source: Literal["real", "synthetic"]


class CustomerSegmentationResponse(BaseModel):
    algorithm: str = "K-Means RFM"
    clusters_count: int
    silhouette_score: float
    inertia: float
    segments: list[CustomerSegmentItem]
    anomalies: list[CustomerAnomalyItem]
    anomalies_count: int
    metrics: MLModelMetrics
    narrative: str


class MLTrainingResponse(BaseModel):
    status: str
    message: str
    supervised_metrics: MLModelMetrics
    unsupervised_metrics: MLModelMetrics


class AudioTranscriptionRequest(BaseModel):
    audio_base64: str
    mime_type: Literal["audio/mp4", "audio/webm"] = "audio/webm"

    @field_validator("audio_base64")
    @classmethod
    def validate_audio_base64(cls, value: str) -> str:
        try:
            decoded = base64.b64decode(value, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("audio_base64 must be strict base64") from exc
        if not decoded:
            raise ValueError("audio_base64 must not be empty")
        if len(decoded) > 2 * 1024 * 1024:
            raise ValueError("decoded audio exceeds the 2 MiB limit")
        return value


class AudioTranscriptionResponse(BaseModel):
    text: str
    confidence: float | None = None
