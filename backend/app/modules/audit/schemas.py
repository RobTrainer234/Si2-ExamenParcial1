from datetime import datetime

from pydantic import BaseModel


class AuditEntryResponse(BaseModel):
    id: int
    user_id: int | None
    user_name: str | None
    action: str
    entity_type: str
    entity_id: int | None
    description: str | None
    old_values: dict | None
    new_values: dict | None
    created_at: datetime


class AuditPage(BaseModel):
    items: list[AuditEntryResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
