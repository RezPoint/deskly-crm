from typing import Optional
from datetime import datetime
from pydantic import Field

from ..schemas.base import APIModel

class ActivityLogOut(APIModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
