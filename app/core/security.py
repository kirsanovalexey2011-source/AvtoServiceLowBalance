from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from app.core.config import settings

_hasher = PasswordHasher()
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="autoflow-session")
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError, TypeError):
        return False

def create_session_token(user_id: int) -> str:
    return _serializer.dumps({"uid": user_id})

def read_session_token(token: str) -> int | None:
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
        user_id = int(data["uid"])
        return user_id if user_id > 0 else None
    except (BadSignature, SignatureExpired, TypeError, ValueError, KeyError):
        return None
