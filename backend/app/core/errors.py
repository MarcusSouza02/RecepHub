import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.services.auth import AuthError

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        # FastAPI's default details include the rejected input and validation context.
        # Operational URLs can contain personal data; do not echo or cache them.
        return JSONResponse(
            status_code=422,
            content={"detail": "Dados da requisição inválidos"},
            headers={"Cache-Control": "no-store"},
        )

    @app.exception_handler(AuthError)
    async def authentication_error(request: Request, error: AuthError) -> JSONResponse:
        from app.api.v1.auth import failure

        return failure(error, request)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, error: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"detail": "Serviço indisponível"},
            headers={"Cache-Control": "no-store"},
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception) -> JSONResponse:
        # Não registrar mensagens de exceção: podem conter URL do banco e dados pessoais.
        logger.error("Erro interno: %s", type(error).__name__)
        return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})
