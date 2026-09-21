from typing import Any
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="Rol del mensaje: user, assistant o system")
    content: str = Field(..., description="Contenido del mensaje")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, description="Pregunta o mensaje del cliente")
    history: list[ChatMessage] = Field(default_factory=list, description="Historial de mensajes previos de la sesión")


class SuggestedProduct(BaseModel):
    id: int
    name: str
    category_name: str
    price: float
    image_url: str | None = None
    slug: str | None = None


class SuggestedAction(BaseModel):
    label: str
    action_type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    reply: str
    suggested_products: list[SuggestedProduct] = Field(default_factory=list)
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    provider: str
