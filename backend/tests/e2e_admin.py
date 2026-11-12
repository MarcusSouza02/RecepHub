"""Only for the disposable real-browser environment; never imported by the app."""

import os
import sys
from datetime import timedelta

from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.orm import Session

from app.core.security import utcnow
from app.models import User, UserSession
from app.services.auth import AuthService
from tests.database import require_test_database_reset, validate_test_database_url


def main():
    require_test_database_reset(os.getenv("TEST_DATABASE_ALLOW_RESET"))
    url = validate_test_database_url(os.environ["TEST_DATABASE_URL"])
    engine = create_engine(url)
    try:
        with Session(engine) as db:
            user = db.scalar(select(User))
            if user is not None and user.username != "e2e.demo":
                raise RuntimeError("Banco contém outra conta; operação recusada")
            if sys.argv[1] == "clean":
                db.execute(delete(User).where(User.username == "e2e.demo"))
                db.commit()
            elif sys.argv[1] == "reset":
                if user is None:
                    AuthService(db).provision("e2e.demo", "Browser-fictional-password-123!")
                else:
                    user.login_attempt_count = 0
                    user.login_window_started_at = None
                    db.commit()
                    AuthService(db).reset_password("Browser-fictional-password-123!")
            elif sys.argv[1] == "expire" and user is not None:
                now = utcnow()
                db.execute(
                    update(UserSession)
                    .where(UserSession.user_id == user.id)
                    .values(
                        created_at=now - timedelta(hours=13),
                        last_seen_at=now - timedelta(hours=3),
                        expires_at=now - timedelta(hours=1),
                    )
                )
                db.commit()
            else:
                raise ValueError("Comando de teste desconhecido")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
