from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Tenant
from ..schemas import TenantOut
from ..auth import get_current_user


router = APIRouter(prefix="/api/tenant", tags=["tenant"])


@router.get("", response_model=TenantOut)
def get_tenant(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    tenant = db.execute(select(Tenant).where(Tenant.id == user.tenant_id)).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    return tenant
