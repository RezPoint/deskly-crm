from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from ..models import Task, Order
from ..schemas.task import TaskCreate, TaskUpdate, TaskOut


class TaskService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def list_tasks(self, order_id: Optional[int] = None, status: Optional[str] = None, limit: int = 200, offset: int = 0) -> List[TaskOut]:
        stmt = select(Task).where(Task.tenant_id == self.tenant_id)

        if order_id is not None:
            stmt = stmt.where(Task.order_id == order_id)
        if status:
            stmt = stmt.where(Task.status == status)

        stmt = stmt.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        tasks = self.db.execute(stmt).scalars().all()

        result = []
        for t in tasks:
            out = TaskOut.model_validate(t)
            if t.order_id:
                order = self.db.get(Order, t.order_id)
                out.order_title = order.title if order else None
            result.append(out)
        return result

    def get_task(self, task_id: int) -> Task:
        t = self.db.execute(
            select(Task).where(Task.id == task_id, Task.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not t:
            raise HTTPException(status_code=404, detail="Task not found")
        return t

    def create_task(self, data: TaskCreate) -> Task:
        t = Task(
            tenant_id=self.tenant_id,
            order_id=data.order_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            status=data.status,
            due_date=data.due_date
        )
        self.db.add(t)
        self.db.commit()
        self.db.refresh(t)
        return t

    def update_task(self, task_id: int, data: TaskUpdate) -> Task:
        t = self.get_task(task_id)

        if data.title is not None:
            t.title = data.title.strip()
        if data.description is not None:
            t.description = data.description.strip()
        if data.status is not None:
            t.status = data.status
        if data.due_date is not None:
            t.due_date = data.due_date
        if data.order_id is not None:
            t.order_id = data.order_id

        self.db.commit()
        self.db.refresh(t)
        return t

    def delete_task(self, task_id: int):
        t = self.get_task(task_id)
        self.db.delete(t)
        self.db.commit()
