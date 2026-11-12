import hashlib
import re
import secrets
from datetime import UTC, datetime

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError

PASSWORD_HASHER = PasswordHasher(
    time_cost=3, memory_cost=65536, parallelism=1, hash_len=32, salt_len=16, type=Type.ID
)
DUMMY_HASH = PASSWORD_HASHER.hash(secrets.token_urlsafe(32))


def utcnow():
    return datetime.now(UTC)


def normalize_username(value: str) -> str:
    value = value.strip().lower()
    if re.fullmatch(r"[a-z0-9._-]{3,80}", value, flags=re.ASCII) is None:
        raise ValueError("Username inválido: use 3–80 caracteres a-z, 0-9, ponto, _ ou -")
    return value


def hash_password(password: str) -> str:
    if not 15 <= len(password) <= 128:
        raise ValueError("A senha deve conter entre 15 e 128 caracteres")
    return PASSWORD_HASHER.hash(password)


def verify_password(encoded: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False


def token_hash(token: str | None) -> str | None:
    if token is None or re.fullmatch(r"[A-Za-z0-9_-]{43}", token, flags=re.ASCII) is None:
        return None
    return hashlib.sha256(token.encode("ascii")).hexdigest()
