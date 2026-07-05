import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from . import models

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str, db: Session = Depends(get_db)) -> Optional[dict]:
    """
    Decode JWT and return user info. Raise 401 if invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    return {"user_id": user_id, "tenant_id": tenant_id, "token": token}


async def get_current_tenant(current_user: dict = Depends(get_current_user)) -> str:
    """Extract tenant_id from token, enforce tenant isolation."""
    if not current_user.get("tenant_id"):
        raise HTTPException(status_code=403, detail="Tenant not found")
    return current_user["tenant_id"]
