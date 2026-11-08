from itsdangerous import BadSignature, URLSafeTimedSerializer
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from app.core.config import settings

_hasher = PasswordHasher()
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="autoflow-session")

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, Exception):
        return False

def create_session_token(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})

def read_session_token(token: str) -> int | None:
    try:
        data = _serializer.loads(token, max_age=60 * 60 * 24 * 7)
        return int(data["uid"])
    except (BadSignature, TypeError, ValueError, KeyError):
        return None
