from typing import List
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...schemas.payment import PaymentCreate, PaymentOut
from ...services.payment_service import PaymentService

router = APIRouter(tags=["payments"])

def get_tenant_id(user: User = Depends(get_current_user)):
    return getattr(user, "tenant_id", 1)

@router.get("/by-order/{order_id}", response_model=List[PaymentOut])
def list_payments(order_id: int = Path(..., ge=1), db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = PaymentService(db, tenant_id)
    return service.list_by_order(order_id)

@router.post("", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = PaymentService(db, tenant_id)
    return service.create_payment(payload)

@router.delete("/{payment_id}", status_code=204)
def delete_payment(payment_id: int = Path(..., ge=1), db: Session = Depends(get_db), tenant_id: int = Depends(get_tenant_id)):
    service = PaymentService(db, tenant_id)
    service.delete_payment(payment_id)
