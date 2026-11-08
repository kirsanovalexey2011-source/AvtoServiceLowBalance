from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_session_token, hash_password, verify_password
from app.models import Organization, User
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/auth", tags=["authentication"])
limiter = Limiter(key_func=get_remote_address)

class RegisterIn(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

def set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        "autoflow_session", create_session_token(user_id),
        httponly=True, secure=settings.app_env == "production",
        samesite="lax", max_age=60 * 60 * 24 * 7, path="/",
    )

@router.post("/register", status_code=201)
@limiter.limit("10/minute")
def register(request: Request, payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Аккаунт с такой почтой уже существует")
    org = Organization(name=payload.organization_name.strip())
    db.add(org)
    db.flush()
    user = User(organization_id=org.id, email=email, password_hash=hash_password(payload.password), role="owner")
    db.add(user)
    db.commit()
    db.refresh(user)
    set_session(response, user.id)
    return {"id": user.id, "email": user.email, "organization": org.name}

@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверная почта или пароль")
    set_session(response, user.id)
    return {"id": user.id, "email": user.email, "organization": user.organization.name}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("autoflow_session", path="/")
    return {"status": "ok"}

@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "organization": user.organization.name, "role": user.role}
