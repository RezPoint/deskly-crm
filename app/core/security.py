import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Set

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from ..models import User

# Отсутствует в Pydantic-settings
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    # простое хеширование (в дальнейшем можно обновить до bcrypt)
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)
) -> User:
    # Поддержка Bearer токена или Cookie
    token = access_token
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Invalid auth token")
        user_id = int(user_id_str)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    request.state.user = user
    return user

def require_role(user: User, allowed_roles: Set[str]) -> None:
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Forbidden")
