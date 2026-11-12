import asyncio
import hashlib
from datetime import timedelta
from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from starlette.requests import Request

from app.api.v1.auth import limited_body, require_auth
from app.core.config import Settings
from app.core.security import hash_password, normalize_username, verify_password
from app.database.session import get_session
from app.main import create_app
from app.models import User, UserSession
from app.services import auth
from app.services.auth import AuthService

PASSWORD = "Fictional-only-password-123!"
HEADERS = {"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"}
LOGIN = "/api/v1/auth/login"
SESSION = "/api/v1/auth/session"
LOGOUT = "/api/v1/auth/logout"


def test_password_hash_and_normalization():
    encoded = hash_password(PASSWORD)
    assert encoded.startswith("$argon2id$v=19$m=65536,t=3,p=1$")
    assert verify_password(encoded, PASSWORD)
    assert not verify_password(encoded, "Wrong-fictional-password")
    assert normalize_username("  DEMO.User  ") == "demo.user"


@pytest.mark.parametrize("password", ["a" * 14, "a" * 129])
def test_password_length(password):
    with pytest.raises(ValueError):
        hash_password(password)


@pytest.mark.parametrize("length", [15, 128])
def test_password_boundaries(length):
    password = " " + "a" * (length - 2) + " "
    encoded = hash_password(password)
    assert verify_password(encoded, password)
    assert not verify_password(encoded, password.strip())


def test_production_requires_https_secure_cookies():
    with pytest.raises(ValueError):
        Settings(_env_file=None, environment="production")
    settings = Settings(
        _env_file=None,
        environment="production",
        auth_secure_cookie=True,
        auth_origin="https://recephub.example",
    )
    assert settings.session_cookie_name == "__Host-recephub_session"


def test_streamed_body_limit_without_content_length():
    chunks = iter([b"a" * 2048, b"a" * 2048, b"a"])

    async def receive():
        return {"type": "http.request", "body": next(chunks), "more_body": True}

    request = Request({"type": "http", "method": "POST", "path": "/", "headers": []}, receive)
    with pytest.raises(auth.AuthError) as caught:
        asyncio.run(limited_body(request))
    assert caught.value.status == 413


@pytest.fixture(scope="module")
def encoded_password():
    return hash_password(PASSWORD)


@pytest.fixture
def account(db_session, encoded_password):
    user = User(username="demo.user", password_hash=encoded_password)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_client(db_session, account):
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as client:
        yield client


def do_login(client, **changes):
    return client.post(
        LOGIN, headers=HEADERS, json={"username": "demo.user", "password": PASSWORD, **changes}
    )


integration = pytest.mark.integration


@integration
def test_login_session_logout(auth_client, db_session):
    response = do_login(auth_client)
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/" in cookie
    assert "Domain=" not in cookie
    token = auth_client.cookies.get("recephub_session")
    stored = db_session.scalars(select(UserSession)).one()
    assert stored.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert token not in response.text
    public = auth_client.get(SESSION)
    assert public.status_code == 200
    assert set(public.json()) == {"user", "expires_at", "idle_expires_at"}
    assert public.headers["cache-control"] == "no-store"
    assert "hash" not in public.text
    assert auth_client.post(LOGOUT, headers=HEADERS, json={}).status_code == 204
    auth_client.cookies.set("recephub_session", token)
    assert auth_client.get(SESSION).status_code == 401
    assert auth_client.post(LOGOUT, headers=HEADERS, json={}).status_code == 204


@integration
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Origin": "null", "X-RecepHub-CSRF": "1"},
        {"Origin": "http://evil.example", "X-RecepHub-CSRF": "1"},
        {"Origin": "http://localhost:3000"},
        {"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "0"},
        [
            ("Origin", "http://localhost:3000"),
            ("Origin", "http://localhost:3000"),
            ("X-RecepHub-CSRF", "1"),
        ],
    ],
)
def test_csrf(auth_client, headers):
    for endpoint in [LOGIN, LOGOUT]:
        response = auth_client.post(endpoint, headers=headers, json={})
        assert response.status_code == 403
        assert "set-cookie" not in response.headers


@integration
def test_json_body_and_sanitized_validation(auth_client, account):
    response = auth_client.post(LOGIN, headers=HEADERS, content="secret-never-echo")
    assert response.status_code == 415
    for data in [{"password": PASSWORD}, {"username": "demo.user", "password": "x" * 129}]:
        response = auth_client.post(LOGIN, headers=HEADERS, json=data)
        assert response.status_code == 422
        assert PASSWORD not in response.text and "xxx" not in response.text
    assert account.login_attempt_count == 0
    response = auth_client.post(
        LOGIN, headers={**HEADERS, "Content-Type": "application/json"}, content=b" " * 4097
    )
    assert response.status_code == 413


@integration
def test_uniform_failure_inactive_unknown_wrong(auth_client, account, db_session):
    wrong = do_login(auth_client, password="Fictional-wrong-password")
    unknown = do_login(auth_client, username="unknown.user")
    account.active = False
    db_session.commit()
    inactive = do_login(auth_client)
    assert wrong.status_code == unknown.status_code == inactive.status_code == 401
    assert wrong.json() == unknown.json() == inactive.json()


@integration
def test_rate_limit_window_and_existing_session(auth_client, account, db_session, monkeypatch):
    now = auth.utcnow()
    monkeypatch.setattr(auth, "utcnow", lambda: now)
    assert do_login(auth_client).status_code == 200
    for i in range(4):
        assert do_login(auth_client, username=f"unknown.{i}").status_code == 401
    limited = do_login(auth_client)
    assert limited.status_code == 429 and int(limited.headers["retry-after"]) == 900
    original_window = account.login_window_started_at
    now += timedelta(seconds=30)
    assert int(do_login(auth_client).headers["retry-after"]) == 870
    db_session.refresh(account)
    assert account.login_window_started_at == original_window
    assert account.login_attempt_count == 5
    assert auth_client.get(SESSION).status_code == 200
    now += timedelta(minutes=14, seconds=30)
    assert do_login(auth_client).status_code == 200
    db_session.refresh(account)
    assert account.login_attempt_count == 1


@integration
@pytest.mark.parametrize("elapsed", [timedelta(hours=2), timedelta(hours=12)])
def test_expiration_boundaries(auth_client, monkeypatch, elapsed):
    now = auth.utcnow()
    monkeypatch.setattr(auth, "utcnow", lambda: now)
    assert do_login(auth_client).status_code == 200
    if elapsed == timedelta(hours=12):
        for _ in range(11):
            now += timedelta(hours=1)
            assert auth_client.get(SESSION).status_code == 200
        now += timedelta(hours=1)
    else:
        now += elapsed
    assert auth_client.get(SESSION).status_code == 401


@integration
def test_devices_rotation_and_password_reset(auth_client, db_session):
    assert do_login(auth_client).status_code == 200
    token_a = auth_client.cookies.get("recephub_session")
    auth_client.cookies.clear()
    assert do_login(auth_client).status_code == 200
    token_b = auth_client.cookies.get("recephub_session")
    assert do_login(auth_client).status_code == 200  # rotate B only
    token_c = auth_client.cookies.get("recephub_session")
    assert token_c != token_b
    service = AuthService(db_session)
    with pytest.raises(auth.AuthError):
        service.current_session(token_b)
    assert service.current_session(token_a)
    service.logout(token_a)
    assert service.current_session(token_c)
    service.reset_password("New-fictional-password-123!")
    with pytest.raises(auth.AuthError):
        service.current_session(token_c)


@integration
def test_provision_duplicate_and_reset(account, db_session):
    service = AuthService(db_session)
    with pytest.raises(ValueError):
        service.provision("second.user", PASSWORD)
    db_session.rollback()


@integration
def test_db_failure_does_not_claim_logout(auth_client, monkeypatch):
    assert do_login(auth_client).status_code == 200

    def fail(*args):
        raise OperationalError("redacted", {}, Exception("secret-database"))

    monkeypatch.setattr(AuthService, "logout", fail)
    response = auth_client.post(LOGOUT, headers=HEADERS, json={})
    assert response.status_code == 503
    assert "set-cookie" not in response.headers
    assert "secret" not in response.text


@integration
def test_unknown_token_and_inactive_session(auth_client, account, db_session):
    auth_client.cookies.set("recephub_session", "a" * 43)
    assert auth_client.get(SESSION).status_code == 401
    auth_client.cookies.clear()
    assert do_login(auth_client).status_code == 200
    account.active = False
    db_session.commit()
    assert auth_client.get(SESSION).status_code == 401


@integration
def test_reusable_guard_protects_endpoint(auth_client):
    @auth_client.app.get("/private-probe")
    async def private_probe(session: Annotated[dict, Depends(require_auth)]):
        return session

    assert auth_client.get("/private-probe").status_code == 401
    assert do_login(auth_client).status_code == 200
    assert auth_client.get("/private-probe").status_code == 200


@integration
def test_production_cookie_attributes_and_deletion(db_session, account):
    app = create_app(
        Settings(
            _env_file=None,
            environment="production",
            auth_secure_cookie=True,
            auth_origin="https://recephub.example",
        )
    )
    app.dependency_overrides[get_session] = lambda: db_session
    headers = {"Origin": "https://recephub.example", "X-RecepHub-CSRF": "1"}
    with TestClient(app, base_url="https://recephub.example") as client:
        response = client.post(
            LOGIN, headers=headers, json={"username": "demo.user", "password": PASSWORD}
        )
        assert response.status_code == 200
        cookie = response.headers["set-cookie"]
        for attribute in [
            "__Host-recephub_session=",
            "Secure",
            "HttpOnly",
            "Path=/",
            "SameSite=lax",
        ]:
            assert attribute in cookie
        assert "Domain=" not in cookie
        response = client.post(LOGOUT, headers=headers, json={})
        assert response.status_code == 204
        assert "__Host-recephub_session=" in response.headers["set-cookie"]
        assert "Max-Age=0" in response.headers["set-cookie"]
