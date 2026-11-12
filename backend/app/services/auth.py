import math
import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.security import (
    DUMMY_HASH,
    PASSWORD_HASHER,
    hash_password,
    normalize_username,
    token_hash,
    utcnow,
    verify_password,
)
from app.models import User, UserSession

ABSOLUTE = timedelta(hours=12)
IDLE = timedelta(hours=2)
WINDOW = timedelta(minutes=15)


class AuthError(Exception):
    def __init__(self, status: int, detail: str, retry_after: int | None = None):
        super().__init__(detail)
        self.status, self.detail, self.retry_after = status, detail, retry_after


def representation(user, session):
    return {
        "user": {"id": str(user.id), "username": user.username},
        "expires_at": session.expires_at,
        "idle_expires_at": min(session.expires_at, session.last_seen_at + IDLE),
    }


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def login(self, username, password, previous_token=None):
        # Reserve the shared attempt in a short transaction before the expensive hash.
        user = self.db.scalar(select(User).with_for_update())
        now = utcnow()
        snapshot = None
        if user is not None:
            if user.login_window_started_at is None or now >= user.login_window_started_at + WINDOW:
                user.login_window_started_at, user.login_attempt_count = now, 0
            if user.login_attempt_count >= 5:
                remaining = math.ceil((user.login_window_started_at + WINDOW - now).total_seconds())
                self.db.commit()
                raise AuthError(
                    429, "Muitas tentativas. Aguarde antes de tentar novamente.", max(1, remaining)
                )
            user.login_attempt_count += 1
            snapshot = (user.id, user.username, user.password_hash, user.active)
        self.db.commit()
        canonical = normalize_username(username)
        matching = snapshot is not None and secrets.compare_digest(canonical, snapshot[1])
        encoded = snapshot[2] if matching else DUMMY_HASH
        valid = verify_password(encoded, password)
        if not matching or not valid or not snapshot[3]:
            raise AuthError(401, "Usuário ou senha inválidos")
        # Recheck password/activity after hash verification: a concurrent reset must win.
        user = self.db.scalar(select(User).where(User.id == snapshot[0]).with_for_update())
        if user is None or not user.active or user.password_hash != snapshot[2]:
            self.db.rollback()
            raise AuthError(401, "Usuário ou senha inválidos")
        now = utcnow()
        if PASSWORD_HASHER.check_needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
        old_hash = token_hash(previous_token)
        if old_hash:
            self.db.execute(
                update(UserSession)
                .where(
                    UserSession.user_id == user.id,
                    UserSession.token_hash == old_hash,
                    UserSession.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
        token = secrets.token_urlsafe(32)
        session = UserSession(
            user_id=user.id,
            token_hash=token_hash(token),
            created_at=now,
            last_seen_at=now,
            expires_at=now + ABSOLUTE,
        )
        self.db.add(session)
        self.db.flush()
        public = representation(user, session)
        self.db.commit()
        return public, token

    def current_session(self, token):
        hashed = token_hash(token)
        if not hashed:
            raise AuthError(401, "Autenticação necessária")
        user = self.db.scalar(select(User).with_for_update())
        session = (
            self.db.scalar(
                select(UserSession).where(UserSession.token_hash == hashed).with_for_update()
            )
            if user
            else None
        )
        now = utcnow()
        if (
            not user
            or not user.active
            or not session
            or session.user_id != user.id
            or session.revoked_at is not None
            or now >= session.expires_at
            or now >= session.last_seen_at + IDLE
        ):
            self.db.rollback()
            raise AuthError(401, "Autenticação necessária")
        session.last_seen_at = max(now, session.last_seen_at)
        public = representation(user, session)
        self.db.commit()
        return public

    def logout(self, token):
        hashed = token_hash(token)
        if not hashed:
            return
        self.db.scalar(select(User).with_for_update())
        self.db.execute(
            update(UserSession)
            .where(UserSession.token_hash == hashed, UserSession.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        self.db.commit()

    def provision(self, username, password):
        canonical, encoded = normalize_username(username), hash_password(password)
        if self.db.scalar(select(User).with_for_update()) is not None:
            raise ValueError("Já existe uma conta provisionada")
        self.db.add(User(username=canonical, password_hash=encoded))
        self.db.commit()

    def reset_password(self, password):
        encoded = hash_password(password)
        user = self.db.scalar(select(User).with_for_update())
        if user is None:
            raise ValueError("Nenhuma conta provisionada")
        user.password_hash = encoded
        self.db.execute(
            update(UserSession)
            .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        self.db.commit()
