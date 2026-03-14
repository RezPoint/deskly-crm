from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import get_current_user
from ...models import User
from ...schemas.product import ProductCreate, ProductUpdate, ProductOut
from ...services.product_service import ProductService

router = APIRouter()

@router.get("", response_model=List[ProductOut])
def list_products(
    q: Optional[str] = None,
    include_inactive: bool = False,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ProductService(db, current_user.tenant_id)
    return service.list_products(q=q, include_inactive=include_inactive, limit=limit, offset=offset)

@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ProductService(db, current_user.tenant_id)
    return service.create_product(data)

@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ProductService(db, current_user.tenant_id)
    return service.update_product(product_id, data)

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ProductService(db, current_user.tenant_id)
    service.delete_product(product_id)
