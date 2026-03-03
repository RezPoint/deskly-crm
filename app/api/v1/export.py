from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...services.export_service import ExportService

router = APIRouter(tags=["export"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

@router.get("/orders.csv")
def export_orders_csv(
    client_id: Optional[int] = Query(None, ge=1),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id)
):
    service = ExportService(db, tenant_id)
    content = service.generate_orders_csv(client_id, status, q, date_from, date_to)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="orders.csv"'},
    )

@router.get("/clients.csv")
def export_clients_csv(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id)
):
    service = ExportService(db, tenant_id)
    content = service.generate_clients_csv()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="clients.csv"'},
    )

@router.get("/templates/clients.csv")
def export_clients_template():
    content = ExportService.generate_clients_template()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="clients_template.csv"'},
    )

@router.get("/templates/orders.csv")
def export_orders_template():
    content = ExportService.generate_orders_template()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="orders_template.csv"'},
    )
