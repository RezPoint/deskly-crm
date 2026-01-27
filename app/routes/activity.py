from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
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
    user_id: Optional[int] = Query(None, ge=1),
    entity_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    stmt = select(ActivityLog).order_by(ActivityLog.id.desc())
    if user_id is not None:
        stmt = stmt.where(ActivityLog.user_id == user_id)
    if entity_type:
        stmt = stmt.where(ActivityLog.entity_type == entity_type)
    stmt = stmt.limit(limit)
    return db.execute(stmt).scalars().all()


@router.get("/ui", response_class=HTMLResponse)
def ui_activity(
    request: Request,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    logs = db.execute(
        select(ActivityLog).order_by(ActivityLog.id.desc()).limit(limit)
    ).scalars().all()
    return templates.TemplateResponse(
        request,
        "activity.html",
        {"request": request, "logs": logs},
    )
