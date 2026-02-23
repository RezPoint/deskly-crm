from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...schemas.analytics import DashboardSummaryOut
from ...services.analytics_service import AnalyticsService

router = APIRouter(tags=["analytics"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

@router.get("/summary", response_model=DashboardSummaryOut)
def get_analytics_summary(db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = AnalyticsService(db, tenant_id)
    return service.get_dashboard_summary()
