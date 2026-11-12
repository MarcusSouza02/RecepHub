import sys

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.cli import auth as cli
from app.core.security import verify_password
from app.models import User
from app.services.auth import AuthError, AuthService

pytestmark = pytest.mark.integration


def test_interactive_create_duplicate_and_reset(migrated_database, monkeypatch, capsys):
    engine = migrated_database
    password = "CLI-fictional-password-123!"
    monkeypatch.setattr(cli, "build_engine", lambda _: engine)
    monkeypatch.setattr("builtins.input", lambda _: " CLI.Demo ")
    monkeypatch.setattr(cli.getpass, "getpass", lambda _: password)
    monkeypatch.setattr(sys, "argv", ["auth", "create"])
    try:
        cli.main()
        with Session(engine) as db:
            user = db.scalar(select(User))
            assert user.username == "cli.demo"
            assert verify_password(user.password_hash, password)
            _, token = AuthService(db).login("cli.demo", password)
        with pytest.raises(SystemExit) as duplicate:
            cli.main()
        assert duplicate.value.code == 1
        password = "Changed-CLI-fictional-password-123!"
        monkeypatch.setattr(sys, "argv", ["auth", "reset-password"])
        cli.main()
        with Session(engine) as db:
            assert verify_password(db.scalar(select(User)).password_hash, password)
            with pytest.raises(AuthError):
                AuthService(db).current_session(token)
        output = capsys.readouterr()
        assert password not in output.out + output.err
        assert token not in output.out + output.err
    finally:
        with Session(engine) as db:
            db.execute(delete(User).where(User.username == "cli.demo"))
            db.commit()
