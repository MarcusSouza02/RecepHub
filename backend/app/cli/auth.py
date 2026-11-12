"""Interactive account administration. Never accept passwords in arguments or env."""

import argparse
import getpass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import build_engine
from app.services.auth import AuthService


def main():
    parser = argparse.ArgumentParser(description="Administração local da conta RecepHub")
    parser.add_argument("action", choices=["create", "reset-password"])
    args = parser.parse_args()
    username = input("Usuário: ") if args.action == "create" else None
    password = getpass.getpass("Nova senha (15–128 caracteres): ")
    if password != getpass.getpass("Confirme a senha: "):
        parser.exit(1, "As senhas não coincidem.\n")
    engine = build_engine(get_settings())
    try:
        with Session(engine) as db:
            service = AuthService(db)
            if args.action == "create":
                service.provision(username, password)
            else:
                service.reset_password(password)
        print("Operação concluída.")
    except ValueError as error:
        parser.exit(1, f"{error}\n")
    except SQLAlchemyError:
        parser.exit(1, "Não foi possível concluir. Confira o banco e a existência da conta.\n")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
