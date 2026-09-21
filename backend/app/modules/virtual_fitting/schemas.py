from datetime import datetime

from pydantic import BaseModel, Field


class VirtualFittingStartRequest(BaseModel):
    product_id: int = Field(gt=0)
    device_info: str | None = Field(default=None, max_length=255)


class VirtualFittingSessionResponse(BaseModel):
    id: int
    customer_id: int | None
    product_id: int
    product_name: str
    image_url: str | None
    status: str
    device_info: str | None
    started_at: datetime
    ended_at: datetime | None


class VirtualFittingListResponse(BaseModel):
    items: list[VirtualFittingSessionResponse]


class VtonTryOnRequest(BaseModel):
    product_id: int = Field(gt=0)
    image_base64: str | None = None
    metrics: dict | None = None


class VtonTryOnResponse(BaseModel):
    product_id: int
    product_name: str
    calce_porcentaje: float | None
    calce_status: str
    alineacion_hombros: str
    proporcion_torso: str
    talla_sugerida: str
    veredicto_estilista: str
    composite_image_base64: str | None
    detalles_tecnicos: dict

