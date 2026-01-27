from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Reminder
from ..schemas import ReminderCreate, ReminderOut, ReminderUpdate, ReminderStatus
from ..auth import get_current_user
from ..activity import log_activity
from .ui import templates


router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderOut])
def list_reminders(
    request: Request,
    status: Optional[ReminderStatus] = None,
    overdue: Optional[bool] = None,
    today: Optional[bool] = None,
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None, ge=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    stmt = (
        select(Reminder)
        .where(Reminder.tenant_id == tenant_id)
        .order_by(Reminder.due_at.asc())
    )
    if status:
        stmt = stmt.where(Reminder.status == status.value)
    if overdue is True:
        stmt = stmt.where(Reminder.status == ReminderStatus.open.value)
        stmt = stmt.where(Reminder.due_at < datetime.utcnow())
    if today is True:
        start = datetime.utcnow().date()
        end = datetime.combine(start, datetime.max.time())
        stmt = stmt.where(Reminder.due_at >= datetime.combine(start, datetime.min.time()))
        stmt = stmt.where(Reminder.due_at <= end)
    if entity_type:
        stmt = stmt.where(Reminder.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(Reminder.entity_id == entity_id)
    stmt = stmt.limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=ReminderOut)
def create_reminder(payload: ReminderCreate, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    r = Reminder(
        tenant_id=tenant_id,
        title=payload.title.strip(),
        due_at=payload.due_at,
        status=ReminderStatus.open.value,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "reminder.created",
        "reminder",
        r.id,
        r.title,
        tenant_id=tenant_id,
    )
    return r


@router.patch("/{reminder_id}", response_model=ReminderOut)
def update_reminder(
    reminder_id: int, payload: ReminderUpdate, request: Request, db: Session = Depends(get_db)
):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    r = db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="reminder not found")
    r.status = payload.status.value
    db.commit()
    db.refresh(r)
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "reminder.status_updated",
        "reminder",
        r.id,
        r.status,
        tenant_id=tenant_id,
    )
    return r


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    r = db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="reminder not found")
    title = r.title
    db.delete(r)
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "reminder.deleted",
        "reminder",
        reminder_id,
        title,
        tenant_id=tenant_id,
    )


@router.get("/ui", response_class=HTMLResponse)
def ui_reminders(
    request: Request,
    status: Optional[str] = Query(None),
    overdue: Optional[str] = Query(None),
    today: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    stmt = (
        select(Reminder)
        .where(Reminder.tenant_id == tenant_id)
        .order_by(Reminder.due_at.asc())
    )
    if status in {"open", "done"}:
        stmt = stmt.where(Reminder.status == status)
    if overdue == "1":
        stmt = stmt.where(Reminder.status == "open")
        stmt = stmt.where(Reminder.due_at < datetime.utcnow())
    if today == "1":
        start = datetime.utcnow().date()
        end = datetime.combine(start, datetime.max.time())
        stmt = stmt.where(Reminder.due_at >= datetime.combine(start, datetime.min.time()))
        stmt = stmt.where(Reminder.due_at <= end)
    if entity_type:
        stmt = stmt.where(Reminder.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(Reminder.entity_id == entity_id)
    reminders = db.execute(stmt).scalars().all()
    open_count = db.execute(
        select(Reminder).where(Reminder.tenant_id == tenant_id, Reminder.status == "open")
    ).scalars().all()
    overdue_count = db.execute(
        select(Reminder)
        .where(Reminder.tenant_id == tenant_id, Reminder.status == "open")
        .where(Reminder.due_at < datetime.utcnow())
    ).scalars().all()
    return templates.TemplateResponse(
        request,
        "reminders.html",
        {
            "request": request,
            "reminders": reminders,
            "filter_status": status or "",
            "filter_overdue": overdue or "",
            "filter_today": today or "",
            "filter_entity_type": entity_type or "",
            "filter_entity_id": entity_id or "",
            "open_count": len(open_count),
            "overdue_count": len(overdue_count),
        },
    )


@router.post("/ui", response_class=RedirectResponse)
def ui_create_reminder(
    request: Request,
    title: str = Form(""),
    due_at: str = Form(""),
    entity_type: Optional[str] = Form(None),
    entity_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    title_clean = (title or "").strip()
    if not title_clean:
        return RedirectResponse(url="/ui/reminders", status_code=303)
    try:
        due_dt = datetime.fromisoformat(due_at)
    except Exception:
        due_dt = datetime.utcnow()
    entity_type_clean = (entity_type or "").strip() or None
    entity_id_clean = int(entity_id) if (entity_id and entity_id.isdigit()) else None
    r = Reminder(
        tenant_id=tenant_id,
        title=title_clean,
        due_at=due_dt,
        status="open",
        entity_type=entity_type_clean,
        entity_id=entity_id_clean,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "reminder.created",
        "reminder",
        r.id,
        r.title,
        tenant_id=tenant_id,
    )
    return RedirectResponse(url="/ui/reminders", status_code=303)


@router.post("/ui/mark-all-done", response_class=RedirectResponse)
def ui_mark_all_done(
    request: Request,
    scope: str = Form("open"),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    stmt = select(Reminder).where(Reminder.tenant_id == tenant_id, Reminder.status == "open")
    if scope == "overdue":
        stmt = stmt.where(Reminder.due_at < datetime.utcnow())
    reminders = db.execute(stmt).scalars().all()
    for r in reminders:
        r.status = "done"
    db.commit()
    user = getattr(request.state, "user", None)
    if user:
        for r in reminders:
            log_activity(
                db,
                getattr(user, "id", None),
                "reminder.status_updated",
                "reminder",
                r.id,
                "done",
                tenant_id=tenant_id,
            )
    return RedirectResponse(url="/ui/reminders", status_code=303)


@router.post("/ui/{reminder_id}/done", response_class=RedirectResponse)
def ui_mark_done(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    r = db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="reminder not found")
    r.status = "done"
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "reminder.status_updated",
        "reminder",
        r.id,
        "done",
        tenant_id=tenant_id,
    )
    return RedirectResponse(url="/ui/reminders", status_code=303)


@router.post("/ui/{reminder_id}/delete", response_class=RedirectResponse)
def ui_delete_reminder(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    tenant_id = getattr(getattr(request.state, "user", None), "tenant_id", 1)
    r = db.execute(
        select(Reminder).where(Reminder.id == reminder_id, Reminder.tenant_id == tenant_id)
    ).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="reminder not found")
    title = r.title
    db.delete(r)
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(
        db,
        getattr(user, "id", None),
        "reminder.deleted",
        "reminder",
        reminder_id,
        title,
        tenant_id=tenant_id,
    )
    return RedirectResponse(url="/ui/reminders", status_code=303)
