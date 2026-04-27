from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...schemas.task import TaskCreate, TaskUpdate, TaskOut
from ...services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=List[TaskOut])
def list_tasks(
    order_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db, current_user.tenant_id)
    return service.list_tasks(order_id=order_id, status=status, limit=limit, offset=offset)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db, current_user.tenant_id)
    task = service.create_task(data)
    # Re-fetch with order title
    return service.list_tasks(order_id=None)[0] if not data.order_id else next(
        (t for t in service.list_tasks() if t.id == task.id), TaskOut.model_validate(task)
    )


@router.put("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db, current_user.tenant_id)
    task = service.update_task(task_id, data)
    # Return with order_title resolved
    result = TaskOut.model_validate(task)
    if task.order_id and task.order:
        result.order_title = task.order.title
    return result


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = TaskService(db, current_user.tenant_id)
    service.delete_task(task_id)
