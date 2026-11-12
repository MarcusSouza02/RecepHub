from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, inspect, select, text, update
from sqlalchemy.exc import DataError, IntegrityError

from app.models import User, UserSession

pytestmark = pytest.mark.integration
CREATED_AT = datetime(2026, 1, 1, 12, tzinfo=UTC)
EXPIRES_AT = CREATED_AT + timedelta(hours=12)
FICTIONAL_HASH = "fixture-only-not-a-real-password-hash"


@pytest.fixture
def user(db_session):
    account = User(username="gerente.demo", password_hash=FICTIONAL_HASH)
    db_session.add(account)
    db_session.flush()
    return account


def make_session(user_id, token_hash="a" * 64, **changes):
    values = {
        "user_id": user_id,
        "token_hash": token_hash,
        "created_at": CREATED_AT,
        "expires_at": EXPIRES_AT,
        "last_seen_at": CREATED_AT,
    }
    values.update(changes)
    return UserSession(**values)


def test_user_defaults_and_uuid(user):
    assert isinstance(user.id, UUID)
    assert user.active is True
    assert user.created_at.tzinfo is not None
    assert user.login_attempt_count == 0
    assert user.login_window_started_at is None


def test_defaults_exist_in_database_not_only_orm(db_session):
    row = db_session.execute(
        text(
            "INSERT INTO users (id, username, password_hash) "
            "VALUES (:id, :username, :hash) "
            "RETURNING active, created_at, login_attempt_count, login_window_started_at"
        ),
        {"id": uuid4(), "username": "conta.teste", "hash": FICTIONAL_HASH},
    ).one()
    assert row.active is True
    assert row.created_at.tzinfo is not None
    assert row.login_attempt_count == 0
    assert row.login_window_started_at is None


@pytest.mark.parametrize("active", [True, False])
def test_single_account_even_when_inactive(db_session, user, active):
    user.active = active
    db_session.flush()
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        db_session.add(User(username="outra.conta", password_hash=FICTIONAL_HASH))
        db_session.flush()
    assert error.value.orig.diag.constraint_name == "uq_users_single_account"


def test_username_unique_constraint_and_duplicate(db_session, user):
    constraints = inspect(db_session.connection()).get_unique_constraints("users")
    assert any(item["column_names"] == ["username"] for item in constraints)
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(User(username=user.username, password_hash=FICTIONAL_HASH))
        db_session.flush()


@pytest.mark.parametrize(
    "username", ["ab", "", "Gerente", " gerente", "gerente ", "gerênte", "a\nb", "user/name"]
)
def test_reject_noncanonical_username(db_session, username):
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        db_session.add(User(username=username, password_hash=FICTIONAL_HASH))
        db_session.flush()
    assert error.value.orig.diag.constraint_name == "ck_users_username_canonical"


@pytest.mark.parametrize("username", ["abc", "a" * 80, "gerente_01.demo-teste"])
def test_username_boundaries_and_allowed_characters(db_session, username):
    db_session.add(User(username=username, password_hash=FICTIONAL_HASH))
    db_session.flush()


def test_reject_username_above_column_limit(db_session):
    with pytest.raises(DataError), db_session.begin_nested():
        db_session.add(User(username="a" * 81, password_hash=FICTIONAL_HASH))
        db_session.flush()


@pytest.mark.parametrize("count", [-1, 6])
def test_reject_attempt_count_outside_approved_range(db_session, user, count):
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        db_session.execute(update(User).where(User.id == user.id).values(login_attempt_count=count))
    assert error.value.orig.diag.constraint_name == "ck_users_login_attempt_count_range"


def test_attempt_count_requires_window(db_session, user):
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        db_session.execute(update(User).where(User.id == user.id).values(login_attempt_count=1))
    assert error.value.orig.diag.constraint_name == "ck_users_login_window_consistent"


def test_accept_window_with_five_attempts(db_session, user):
    user.login_attempt_count = 5
    user.login_window_started_at = CREATED_AT
    db_session.flush()


def test_multiple_sessions_and_relationship(db_session, user):
    first = make_session(user.id)
    second = make_session(user.id, token_hash="b" * 64)
    db_session.add_all([first, second])
    db_session.flush()
    db_session.expire_all()
    assert first.id != second.id
    assert isinstance(first.id, UUID)
    assert first.user is user
    assert {item.id for item in user.sessions} == {first.id, second.id}
    assert first.created_at.tzinfo is not None
    assert first.revoked_at is None


def test_session_has_only_hash_column(db_session, user):
    columns = {
        item["name"] for item in inspect(db_session.connection()).get_columns("user_sessions")
    }
    assert columns == {
        "id",
        "user_id",
        "token_hash",
        "created_at",
        "expires_at",
        "last_seen_at",
        "revoked_at",
    }
    record = make_session(user.id)
    db_session.add(record)
    db_session.flush()
    assert db_session.scalar(select(UserSession.token_hash)) == "a" * 64


def test_session_database_timestamp_defaults(db_session, user):
    row = db_session.execute(
        text(
            "INSERT INTO user_sessions (id, user_id, token_hash, expires_at) "
            "VALUES (:id, :user_id, :hash, CURRENT_TIMESTAMP + interval '12 hours') "
            "RETURNING created_at, last_seen_at, revoked_at"
        ),
        {"id": uuid4(), "user_id": user.id, "hash": "a" * 64},
    ).one()
    assert row.created_at.tzinfo is not None
    assert row.created_at == row.last_seen_at
    assert row.revoked_at is None


def test_reject_session_for_missing_user(db_session):
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        db_session.add(make_session(uuid4()))
        db_session.flush()
    assert error.value.orig.diag.constraint_name == "fk_user_sessions_user_id_users"


def test_reject_duplicate_session_hash(db_session, user):
    db_session.add(make_session(user.id))
    db_session.flush()
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        db_session.add(make_session(user.id))
        db_session.flush()
    assert error.value.orig.diag.constraint_name == "uq_user_sessions_token_hash"


@pytest.mark.parametrize("token_hash", ["", "a" * 63, "g" * 64, "A" * 64])
def test_reject_malformed_hash(db_session, user, token_hash):
    with pytest.raises(IntegrityError) as error, db_session.begin_nested():
        db_session.add(make_session(user.id, token_hash=token_hash))
        db_session.flush()
    assert error.value.orig.diag.constraint_name == "ck_user_sessions_token_hash_format"


def test_reject_hash_above_column_limit(db_session, user):
    with pytest.raises(DataError), db_session.begin_nested():
        db_session.add(make_session(user.id, token_hash="a" * 65))
        db_session.flush()


@pytest.mark.parametrize(
    "changes",
    [
        {"expires_at": CREATED_AT},
        {"expires_at": CREATED_AT - timedelta(seconds=1)},
        {"last_seen_at": CREATED_AT - timedelta(seconds=1)},
        {"last_seen_at": EXPIRES_AT},
        {"last_seen_at": EXPIRES_AT + timedelta(seconds=1)},
        {"revoked_at": CREATED_AT - timedelta(seconds=1)},
    ],
)
def test_reject_inconsistent_session_times(db_session, user, changes):
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(make_session(user.id, **changes))
        db_session.flush()


def test_revocation_preserves_other_device_session(db_session, user):
    revoked = make_session(user.id, revoked_at=CREATED_AT + timedelta(hours=1))
    other = make_session(user.id, token_hash="b" * 64)
    db_session.add_all([revoked, other])
    db_session.flush()
    assert other.revoked_at is None
    assert len(user.sessions) == 2


def test_database_delete_cascades_without_orm_loading(db_session, user):
    db_session.add(make_session(user.id))
    db_session.flush()
    db_session.execute(delete(User).where(User.id == user.id))
    assert db_session.scalars(select(UserSession)).all() == []


def test_indexes_and_foreign_key(db_session):
    inspector = inspect(db_session.connection())
    indexes = {item["name"]: item for item in inspector.get_indexes("users")}
    assert indexes["uq_users_single_account"]["unique"] is True
    assert "ix_user_sessions_user_id" in {
        item["name"] for item in inspector.get_indexes("user_sessions")
    }
    foreign_key = inspector.get_foreign_keys("user_sessions")[0]
    assert foreign_key["options"]["ondelete"] == "CASCADE"
