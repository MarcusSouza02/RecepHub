import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, error: Exception) -> JSONResponse:
        # Não registrar mensagens de exceção: podem conter URL do banco e dados pessoais.
        logger.error("Erro interno: %s", type(error).__name__)
        return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})
