import hashlib, hmac, secrets
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings

_ITERATIONS = 2**14

def hash_secret(secret: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(secret.encode(), salt=salt, n=_ITERATIONS, r=8, p=1)
    return f"scrypt${_ITERATIONS}${salt.hex()}${derived.hex()}"

def verify_secret(secret: str, encoded: str) -> bool:
    try:
        scheme, n_value, salt_hex, digest_hex = encoded.split("$", 3)
        if scheme != "scrypt": return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(secret.encode(), salt=bytes.fromhex(salt_hex), n=int(n_value), r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def create_access_token(subject: str, token_type: str, minutes: int, extra: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "type": token_type, "iat": now, "exp": now + timedelta(minutes=minutes)}
    if extra: payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
