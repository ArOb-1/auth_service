import uuid
import bcrypt
import jwt

from datetime import datetime, timedelta, timezone
from core.settings import JWT_SECRET


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def generate_access_token(user_id: str, role: str) -> str:
    payload = {
        'user_id': str(user_id),
        'role': role,
        'type': 'access',
        'exp': datetime.now(timezone.utc) + timedelta(minutes=15),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def generate_refresh_token(user_id: str) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {
        'user_id': str(user_id),
        'type':    'refresh',
        'jti':     str(uuid.uuid4()),
        'exp':     expires_at,
        'iat':     datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token, expires_at


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
