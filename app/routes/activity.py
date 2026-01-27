from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActivityLog
from ..schemas import ActivityLogOut
from ..auth import get_current_user
from .ui import templates


router = APIRouter(prefix="/api/activity", tags=["activity"])


@router.get("", response_model=list[ActivityLogOut])
def list_activity(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: Optional[int] = Query(None, ge=1),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.tenant_id == tenant_id)
        .order_by(ActivityLog.id.desc())
    )
    if user_id is not None:
        stmt = stmt.where(ActivityLog.user_id == user_id)
    if entity_type:
        stmt = stmt.where(ActivityLog.entity_type == entity_type)
    if action:
        stmt = stmt.where(ActivityLog.action == action)
    if date_from:
        stmt = stmt.where(ActivityLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(ActivityLog.created_at <= date_to)
    stmt = stmt.limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@router.get("/ui", response_class=HTMLResponse)
def ui_activity(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: Optional[int] = Query(None),
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.tenant_id == tenant_id)
        .order_by(ActivityLog.id.desc())
    )
    if user_id:
        stmt = stmt.where(ActivityLog.user_id == user_id)
    if entity_type:
        stmt = stmt.where(ActivityLog.entity_type == entity_type)
    if action:
        stmt = stmt.where(ActivityLog.action == action)
    if date_from:
        stmt = stmt.where(ActivityLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(ActivityLog.created_at <= date_to)
    total_count = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    logs = db.execute(stmt.limit(limit).offset(offset)).scalars().all()
    page = (offset // limit) + 1
    total_pages = max(1, (total_count + limit - 1) // limit)
    return templates.TemplateResponse(
        request,
        "activity.html",
        {
            "request": request,
            "logs": logs,
            "filter_user_id": user_id or "",
            "filter_entity_type": entity_type or "",
            "filter_action": action or "",
            "filter_date_from": date_from or "",
            "filter_date_to": date_to or "",
            "page": page,
            "total_pages": total_pages,
            "limit": limit,
            "offset": offset,
        },
    )
