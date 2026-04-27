from typing import Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal

from ..models import Product
from ..schemas.product import ProductCreate, ProductUpdate

class ProductService:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def list_products(self, q: Optional[str] = None, include_inactive: bool = False, limit: int = 100, offset: int = 0):
        stmt = select(Product).where(Product.tenant_id == self.tenant_id)
        
        if not include_inactive:
            stmt = stmt.where(Product.is_active == 1)
            
        if q:
            s = f"%{q.strip()}%"
            stmt = stmt.where(or_(Product.name.ilike(s), Product.description.ilike(s)))
            
        stmt = stmt.order_by(Product.name.asc())
        return self.db.execute(stmt.limit(limit).offset(offset)).scalars().all()

    def get_product(self, product_id: int) -> Product:
        p = self.db.execute(
            select(Product).where(Product.id == product_id, Product.tenant_id == self.tenant_id)
        ).scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="Product not found")
        return p

    def create_product(self, data: ProductCreate) -> Product:
        p = Product(
            tenant_id=self.tenant_id,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            price=data.price,
            is_active=1 if data.is_active else 0
        )
        self.db.add(p)
        self.db.commit()
        self.db.refresh(p)
        return p

    def update_product(self, product_id: int, data: ProductUpdate) -> Product:
        p = self.get_product(product_id)
        
        if data.name is not None:
            p.name = data.name.strip()
        if data.description is not None:
            p.description = data.description.strip()
        if data.price is not None:
            p.price = data.price
        if data.is_active is not None:
            p.is_active = 1 if data.is_active else 0
            
        self.db.commit()
        self.db.refresh(p)
        return p

    def delete_product(self, product_id: int):
        p = self.get_product(product_id)
        self.db.delete(p)
        self.db.commit()
