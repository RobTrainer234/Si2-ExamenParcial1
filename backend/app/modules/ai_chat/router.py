from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.ai_chat import service
from app.modules.ai_chat.schemas import ChatRequest, ChatResponse
from app.modules.auth.dependencies import bind_optional_tenant_context

router = APIRouter(prefix="/ai", tags=["ai-chat"], dependencies=[Depends(bind_optional_tenant_context)])


@router.post("/chat", response_model=ChatResponse)
def ai_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint del Asistente Virtual Inteligente (Chatbot IA) de FashionStore.
    Permite a los clientes recibir recomendaciones en lenguaje natural,
    consultar sobre sucursales, vestidor virtual y promociones vigentes.
    """
    return service.process_chat(db, request)
