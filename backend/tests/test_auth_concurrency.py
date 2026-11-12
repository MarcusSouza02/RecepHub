from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User, UserSession
from app.services import auth
from app.services.auth import AuthError, AuthService

pytestmark = pytest.mark.integration
PASSWORD = "Concurrency-fictional-password-123!"


@pytest.fixture
def committed_account(migrated_database):
    with Session(migrated_database) as db:
        user = User(username="concurrency.demo", password_hash=hash_password(PASSWORD))
        db.add(user)
        db.commit()
        account_id = user.id
    try:
        yield migrated_database, account_id
    finally:
        with Session(migrated_database) as db:
            db.execute(delete(User).where(User.id == account_id))
            db.commit()


def test_parallel_attempts_share_persistent_limit(committed_account):
    engine, account_id = committed_account
    barrier = Barrier(6)

    def attempt():
        barrier.wait(timeout=10)
        with Session(engine) as db:
            try:
                AuthService(db).login("unknown.user", PASSWORD)
            except AuthError as error:
                return error.status

    with ThreadPoolExecutor(max_workers=6) as executor:
        statuses = list(executor.map(lambda _: attempt(), range(6)))
    assert statuses.count(401) == 5
    assert statuses.count(429) == 1
    # New engine connection represents another worker/restart: no in-memory state.
    with Session(engine) as db:
        assert db.get(User, account_id).login_attempt_count == 5
        assert db.scalar(select(UserSession)) is None


def test_reset_during_verification_blocks_old_password(committed_account, monkeypatch):
    engine, _ = committed_account
    verifying, resume = Event(), Event()
    real_verify = auth.verify_password

    def delayed_verify(encoded, password):
        verifying.set()
        assert resume.wait(timeout=15)
        return real_verify(encoded, password)

    monkeypatch.setattr(auth, "verify_password", delayed_verify)

    def login():
        with Session(engine) as db:
            try:
                AuthService(db).login("concurrency.demo", PASSWORD)
            except AuthError as error:
                return error.status

    with ThreadPoolExecutor(max_workers=1) as executor:
        task = executor.submit(login)
        try:
            assert verifying.wait(timeout=15)
            with Session(engine) as db:
                AuthService(db).reset_password("Changed-fictional-password-123!")
        finally:
            resume.set()
        assert task.result(timeout=15) == 401


@pytest.mark.parametrize("operation", ["logout", "reset"])
def test_revocation_wins_against_concurrent_session_read(committed_account, operation):
    engine, _ = committed_account
    with Session(engine) as db:
        _, token = AuthService(db).login("concurrency.demo", PASSWORD)
    started = Event()

    def read_session():
        with Session(engine) as db:
            started.set()
            try:
                AuthService(db).current_session(token)
            except AuthError as error:
                return error.status

    with Session(engine) as revoker, ThreadPoolExecutor(max_workers=1) as executor:
        revoker.scalar(select(User).with_for_update())
        task = executor.submit(read_session)
        assert started.wait(timeout=10)
        if operation == "logout":
            AuthService(revoker).logout(token)
        else:
            AuthService(revoker).reset_password("Changed-fictional-password-123!")
        assert task.result(timeout=15) == 401
    with Session(engine) as db:
        assert db.scalar(select(UserSession)).revoked_at is not None
