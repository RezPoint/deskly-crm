import csv
from io import StringIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...services.import_service import ImportService
from ...services.activity_service import ActivityService

router = APIRouter(tags=["import"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

def get_user_id(user: User = Depends(get_current_user)):
    return getattr(user, "id", None)

def _read_csv(upload: UploadFile) -> list[dict]:
    if not upload.filename or not upload.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="file must be .csv")
    data = upload.file.read()
    try:
        text = data.decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=422, detail="file must be UTF-8 CSV")
    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status_code=422, detail="missing CSV header")
    rows = []
    for row in reader:
        if any((v or "").strip() for v in row.values()):
            rows.append({k: (v or "").strip() for k, v in row.items()})
    return rows

@router.post("/clients")
def import_clients(
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    user_id: int = Depends(get_user_id)
):
    rows = _read_csv(file)
    if not rows:
        return {"created": 0}

    service = ImportService(db, tenant_id)
    created, errors = service.process_clients(rows, user_id)

    if errors:
        db.rollback()
        raise HTTPException(status_code=422, detail=errors)

    if dry_run:
        db.rollback()
        return {"created": created, "dry_run": True}

    db.commit()
    if created > 0 and user_id:
        act_svc = ActivityService(db, tenant_id)
        for _ in range(created):
            act_svc.log_action(user_id, "client.created", "client", message="CSV import")
    return {"created": created}

@router.post("/orders")
def import_orders(
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
    user_id: int = Depends(get_user_id)
):
    rows = _read_csv(file)
    if not rows:
        return {"created": 0}

    service = ImportService(db, tenant_id)
    created, errors = service.process_orders(rows, user_id)

    if errors:
        db.rollback()
        raise HTTPException(status_code=422, detail=errors)

    if dry_run:
        db.rollback()
        return {"created": created, "dry_run": True}

    db.commit()
    if created > 0 and user_id:
        act_svc = ActivityService(db, tenant_id)
        for _ in range(created):
            act_svc.log_action(user_id, "order.created", "order", message="CSV import")
    return {"created": created}
