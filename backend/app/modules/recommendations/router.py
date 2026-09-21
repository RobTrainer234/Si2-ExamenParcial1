from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.database import get_db
from app.core.models import User
from app.modules.auth.dependencies import require_permission
from app.modules.recommendations import service
from app.modules.recommendations.schemas import RecommendationResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
RecommendationClient = Annotated[User, Depends(require_permission("recommendations.read"))]


@router.get("/mine", response_model=RecommendationResponse)
def mine(current_user: RecommendationClient, limit: int = Query(8, ge=1, le=20), db=Depends(get_db)):
    result = service.recommend(db, current_user, limit)
    db.commit()
    return result
