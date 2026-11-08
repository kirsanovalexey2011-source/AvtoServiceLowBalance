from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import re
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_current_user, get_db, get_optional_current_user
from app.core.config import settings
from app.core.security import create_session_token, hash_password, verify_password
from app.models import EmailVerification, Organization, User
from app.services.mailer import send_verification_email

router = APIRouter(prefix="/api/auth", tags=["authentication"])
limiter = Limiter(key_func=get_remote_address)
verification_signer = URLSafeTimedSerializer(settings.secret_key, salt="autoflow-email-verification")
CODE_TTL = timedelta(minutes=10)
TOKEN_TTL_SECONDS = 15 * 60
MAX_CODE_ATTEMPTS = 5


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _code_digest(email: str, purpose: str, code: str) -> str:
    payload = f"autoflow-email-code:{email}:{purpose}:{code}".encode("utf-8")
    return hmac.new(settings.secret_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _is_expired(value: datetime) -> bool:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= utcnow()


def _consume_registration_token(token: str | None, email: str, db: Session) -> bool:
    if not token:
        if settings.app_env.lower() == "production":
            raise HTTPException(status_code=400, detail="Подтвердите email кодом из письма")
        return False
    try:
        data = verification_signer.loads(token, max_age=TOKEN_TTL_SECONDS)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=400, detail="Подтверждение недействительно или устарело")
    if data.get("purpose") != "registration" or data.get("email") != email:
        raise HTTPException(status_code=400, detail="Подтверждение не относится к этой почте")
    challenge = db.get(EmailVerification, data.get("challenge_id"))
    if not challenge or challenge.purpose != "registration" or challenge.email != email:
        raise HTTPException(status_code=400, detail="Подтверждение не найдено")
    if not challenge.verified_at or challenge.consumed_at or _is_expired(challenge.expires_at):
        raise HTTPException(status_code=400, detail="Код уже использован или срок его действия истёк")
    challenge.consumed_at = utcnow()
    return True


class RegisterIn(BaseModel):
    organization_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    email_verification_token: str | None = Field(default=None, max_length=2048)

    @field_validator("organization_name")
    @classmethod
    def organization_name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Название организации должно содержать минимум 2 символа")
        return value


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class EmailCodeRequestIn(BaseModel):
    email: EmailStr
    purpose: Literal["registration", "account"] = "registration"


class EmailCodeVerifyIn(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")
    purpose: Literal["registration", "account"] = "registration"


class ProfileUpdateIn(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=32)

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if value and len(value) < 2:
            raise ValueError("Имя должно содержать минимум 2 символа")
        return value or None

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = re.sub(r"[\s()-]", "", value.strip())
        if not value:
            return None
        if not re.fullmatch(r"\+?\d{7,15}", value):
            raise ValueError("Введите номер телефона в международном формате, например +79991234567")
        return value


def set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        "autoflow_session", create_session_token(user_id),
        httponly=True, secure=settings.app_env == "production",
        samesite="lax", max_age=60 * 60 * 24 * 7, path="/",
    )


@router.post("/email-code")
@limiter.limit("10/hour")
def request_email_code(
    request: Request,
    payload: EmailCodeRequestIn,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    email = str(payload.email).strip().lower()
    purpose = payload.purpose
    if purpose == "registration":
        if db.scalar(select(User.id).where(User.email == email)):
            raise HTTPException(status_code=409, detail="Аккаунт с такой почтой уже существует. Войдите в него.")
    else:
        if not current_user:
            raise HTTPException(status_code=401, detail="Войдите, чтобы подтвердить почту аккаунта")
        if current_user.email.lower() != email:
            raise HTTPException(status_code=403, detail="Можно подтвердить только почту текущего аккаунта")

    now = utcnow()
    latest = db.scalar(select(EmailVerification).where(
        EmailVerification.email == email,
        EmailVerification.purpose == purpose,
    ).order_by(EmailVerification.created_at.desc()).limit(1))
    if latest and not _is_expired(latest.created_at + timedelta(seconds=60)):
        raise HTTPException(status_code=429, detail="Новый код можно запросить через минуту")

    recent_count = db.scalar(select(func.count(EmailVerification.id)).where(
        EmailVerification.email == email,
        EmailVerification.purpose == purpose,
        EmailVerification.created_at >= now - timedelta(hours=1),
    )) or 0
    if recent_count >= 5:
        raise HTTPException(status_code=429, detail="Лимит отправки кодов для этой почты исчерпан. Попробуйте позже")

    for previous in db.scalars(select(EmailVerification).where(
        EmailVerification.email == email,
        EmailVerification.purpose == purpose,
        EmailVerification.consumed_at.is_(None),
    )):
        previous.consumed_at = now

    code = f"{secrets.randbelow(900000) + 100000:06d}"
    challenge = EmailVerification(
        email=email,
        purpose=purpose,
        code_hash=_code_digest(email, purpose, code),
        expires_at=now + CODE_TTL,
        created_at=now,
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    try:
        send_verification_email(email, code, purpose)
    except Exception:
        challenge.consumed_at = utcnow()
        db.commit()
        raise HTTPException(status_code=503, detail="Не удалось отправить письмо. Проверьте SMTP-настройки сервера")
    return {
        "status": "sent",
        "expires_in_seconds": int(CODE_TTL.total_seconds()),
        "message": "Код отправлен на указанную почту",
    }


@router.post("/verify-email-code")
@limiter.limit("20/minute")
def verify_email_code(
    request: Request,
    payload: EmailCodeVerifyIn,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    email = str(payload.email).strip().lower()
    purpose = payload.purpose
    if purpose == "account":
        if not current_user:
            raise HTTPException(status_code=401, detail="Войдите в аккаунт")
        if current_user.email.lower() != email:
            raise HTTPException(status_code=403, detail="Можно подтвердить только почту текущего аккаунта")

    challenge = db.scalar(select(EmailVerification).where(
        EmailVerification.email == email,
        EmailVerification.purpose == purpose,
        EmailVerification.consumed_at.is_(None),
    ).order_by(EmailVerification.created_at.desc()).limit(1))
    if not challenge:
        raise HTTPException(status_code=400, detail="Сначала запросите код подтверждения")
    if _is_expired(challenge.expires_at):
        challenge.consumed_at = utcnow()
        db.commit()
        raise HTTPException(status_code=400, detail="Срок действия кода истёк. Запросите новый")
    if challenge.attempts >= MAX_CODE_ATTEMPTS:
        challenge.consumed_at = utcnow()
        db.commit()
        raise HTTPException(status_code=429, detail="Превышено число попыток. Запросите новый код")
    expected = _code_digest(email, purpose, payload.code)
    if not hmac.compare_digest(challenge.code_hash, expected):
        challenge.attempts += 1
        if challenge.attempts >= MAX_CODE_ATTEMPTS:
            challenge.consumed_at = utcnow()
        db.commit()
        raise HTTPException(status_code=400, detail="Неверный код")

    challenge.verified_at = utcnow()
    if purpose == "account":
        current_user.email_verified_at = challenge.verified_at
        challenge.consumed_at = challenge.verified_at
        db.commit()
        return {"verified": True, "message": "Почта аккаунта подтверждена"}

    db.commit()
    token = verification_signer.dumps({
        "email": email,
        "purpose": "registration",
        "challenge_id": challenge.id,
    })
    return {
        "verified": True,
        "verification_token": token,
        "message": "Почта подтверждена. Теперь завершите регистрацию",
    }


@router.post("/register", status_code=201)
@limiter.limit("10/minute")
def register(request: Request, payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Аккаунт с такой почтой уже существует")
    email_verified = _consume_registration_token(payload.email_verification_token, email, db)
    org = Organization(name=payload.organization_name.strip())
    db.add(org)
    db.flush()
    user = User(
        organization_id=org.id,
        email=email,
        password_hash=hash_password(payload.password),
        role="owner",
        email_verified_at=utcnow() if email_verified else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    set_session(response, user.id)
    return {
        "id": user.id,
        "email": user.email,
        "organization": org.name,
        "email_verified": user.email_verified_at is not None,
    }


@router.post("/login")
@limiter.limit("10/minute")
def login(request: Request, payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверная почта или пароль")
    set_session(response, user.id)
    return {
        "id": user.id,
        "email": user.email,
        "organization": user.organization.name,
        "email_verified": user.email_verified_at is not None,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("autoflow_session", path="/")
    return {"status": "ok"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "organization": user.organization.name,
        "role": user.role,
        "email_verified": user.email_verified_at is not None,
        "phone": user.phone,
        "full_name": user.full_name,
    }


@router.get("/profile")
def get_profile(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "email_verified": user.email_verified_at is not None,
        "full_name": user.full_name,
        "phone": user.phone,
        "phone_verified": user.phone_verified_at is not None,
        "organization": user.organization.name,
    }


@router.patch("/profile")
def update_profile(
    payload: ProfileUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    changes = payload.model_dump(exclude_unset=True)
    if "phone" in changes and changes["phone"] != user.phone:
        user.phone = changes["phone"]
        user.phone_verified_at = None
    if "full_name" in changes:
        user.full_name = changes["full_name"]
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "email": user.email,
        "email_verified": user.email_verified_at is not None,
        "full_name": user.full_name,
        "phone": user.phone,
        "phone_verified": user.phone_verified_at is not None,
    }
