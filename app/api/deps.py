from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import read_session_token
from app.models import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(autoflow_session: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    user_id = read_session_token(autoflow_session) if autoflow_session else None
    user = db.get(User, user_id) if user_id else None
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется вход")
    return user
