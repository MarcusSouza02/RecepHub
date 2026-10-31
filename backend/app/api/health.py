from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.schemas.health import HealthResponse, ReadyResponse

health_router = APIRouter(tags=["health"])
ready_router = APIRouter(tags=["health"])


@health_router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@ready_router.get("/health/ready", response_model=ReadyResponse)
def ready(session: Session = Depends(get_session)) -> ReadyResponse:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível") from None
    return ReadyResponse()
