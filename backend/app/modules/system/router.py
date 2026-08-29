from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.database import check_database_connection

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> JSONResponse:
    database_available = check_database_connection()
    response_status = "ok" if database_available else "degraded"
    http_status = status.HTTP_200_OK if database_available else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=http_status,
        content={"status": response_status, "database": "ok" if database_available else "unavailable"},
    )
