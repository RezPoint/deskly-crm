from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
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
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    stmt = select(Reminder).order_by(Reminder.due_at.asc())
    if status:
        stmt = stmt.where(Reminder.status == status.value)
    if overdue is True:
        stmt = stmt.where(Reminder.status == ReminderStatus.open.value)
        stmt = stmt.where(Reminder.due_at < datetime.utcnow())
    stmt = stmt.limit(limit)
    return db.execute(stmt).scalars().all()


@router.post("", response_model=ReminderOut)
def create_reminder(payload: ReminderCreate, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    r = Reminder(
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
    log_activity(db, getattr(user, "id", None), "reminder.created", "reminder", r.id, r.title)
    return r


@router.patch("/{reminder_id}", response_model=ReminderOut)
def update_reminder(
    reminder_id: int, payload: ReminderUpdate, request: Request, db: Session = Depends(get_db)
):
    get_current_user(request, db)
    r = db.execute(select(Reminder).where(Reminder.id == reminder_id)).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="reminder not found")
    r.status = payload.status.value
    db.commit()
    db.refresh(r)
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "reminder.status_updated", "reminder", r.id, r.status)
    return r


@router.delete("/{reminder_id}", status_code=204)
def delete_reminder(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    r = db.execute(select(Reminder).where(Reminder.id == reminder_id)).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="reminder not found")
    title = r.title
    db.delete(r)
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "reminder.deleted", "reminder", reminder_id, title)


@router.get("/ui", response_class=HTMLResponse)
def ui_reminders(
    request: Request,
    status: Optional[str] = Query(None),
    overdue: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    stmt = select(Reminder).order_by(Reminder.due_at.asc())
    if status in {"open", "done"}:
        stmt = stmt.where(Reminder.status == status)
    if overdue == "1":
        stmt = stmt.where(Reminder.status == "open")
        stmt = stmt.where(Reminder.due_at < datetime.utcnow())
    reminders = db.execute(stmt).scalars().all()
    return templates.TemplateResponse(
        request,
        "reminders.html",
        {
            "request": request,
            "reminders": reminders,
            "filter_status": status or "",
            "filter_overdue": overdue or "",
        },
    )


@router.post("/ui", response_class=RedirectResponse)
def ui_create_reminder(
    request: Request,
    title: str = Query(""),
    due_at: str = Query(""),
    db: Session = Depends(get_db),
):
    get_current_user(request, db)
    title_clean = (title or "").strip()
    if not title_clean:
        return RedirectResponse(url="/ui/reminders", status_code=303)
    try:
        due_dt = datetime.fromisoformat(due_at)
    except Exception:
        due_dt = datetime.utcnow()
    r = Reminder(title=title_clean, due_at=due_dt, status="open")
    db.add(r)
    db.commit()
    db.refresh(r)
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "reminder.created", "reminder", r.id, r.title)
    return RedirectResponse(url="/ui/reminders", status_code=303)


@router.post("/ui/{reminder_id}/done", response_class=RedirectResponse)
def ui_mark_done(reminder_id: int, request: Request, db: Session = Depends(get_db)):
    get_current_user(request, db)
    r = db.execute(select(Reminder).where(Reminder.id == reminder_id)).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=404, detail="reminder not found")
    r.status = "done"
    db.commit()
    user = getattr(request.state, "user", None)
    log_activity(db, getattr(user, "id", None), "reminder.status_updated", "reminder", r.id, "done")
    return RedirectResponse(url="/ui/reminders", status_code=303)
