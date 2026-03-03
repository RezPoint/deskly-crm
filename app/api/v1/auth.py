from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.security import verify_password, create_access_token, get_current_user
from ...models import User, Tenant
from ...schemas.auth import LoginIn
from ...services.user_service import UserService
from pydantic import BaseModel

class SetupInput(BaseModel):
    email: str
    password: str
    workspace: str = "Default"

router = APIRouter(tags=["auth"])

def _has_users(db: Session) -> bool:
    return db.execute(select(User.id)).first() is not None

@router.get("/has-users")
def check_has_users(db: Session = Depends(get_db)):
    return {"has_users": _has_users(db)}

@router.post("/setup")
def setup_submit(payload: SetupInput, db: Session = Depends(get_db)):
    if _has_users(db):
        raise HTTPException(status_code=409, detail="Setup already completed")
    
    user = UserService.setup_account(db, payload.email, payload.password, payload.workspace)
    return {"detail": "Setup successful", "user_id": user.id}

@router.post("/login")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    token = create_access_token(user.id, user.role)
    
    # Отправляем токен как в JSON, так и в HttpOnly cookie для веб SPA
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return {"access_token": token, "token_type": "bearer", "role": user.role, "email": user.email}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"detail": "Successfully logged out"}

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role, "tenant_id": user.tenant_id}
