import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.core.security import normalize_username
from app.database.session import get_session
from app.services.auth import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
Database = Annotated[Session, Depends(get_session)]


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    username: str = Field(min_length=3, max_length=256)
    password: str = Field(min_length=15, max_length=128, repr=False)

    @field_validator("username")
    @classmethod
    def canonical(cls, value):
        return normalize_username(value)


def response_json(content, status=200):
    return JSONResponse(
        jsonable_encoder(content),
        status_code=status,
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


def clear_cookie(response, settings):
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.auth_secure_cookie,
        samesite="lax",
    )


def failure(error, request):
    response = response_json({"detail": error.detail}, error.status)
    if error.retry_after is not None:
        response.headers["Retry-After"] = str(error.retry_after)
    return response


def guard_write(request):
    settings = request.app.state.settings
    if request.headers.getlist("origin") != [settings.auth_origin] or request.headers.getlist(
        "x-recephub-csrf"
    ) != ["1"]:
        raise AuthError(403, "Origem ou proteção CSRF inválida")
    types = request.headers.getlist("content-type")
    if len(types) != 1 or types[0].split(";", 1)[0].strip().lower() != "application/json":
        raise AuthError(415, "Envie application/json")


async def limited_body(request):
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > 4096:
            raise AuthError(413, "Corpo excede 4 KiB")
        data.extend(chunk)
    return bytes(data)


@router.post("/login")
async def login(request: Request, db: Database):
    try:
        guard_write(request)
        body = await limited_body(request)
        try:
            payload = LoginInput.model_validate(json.loads(body))
        except (ValidationError, ValueError, UnicodeDecodeError):
            raise AuthError(422, "Dados de login inválidos") from None
        settings = request.app.state.settings
        public, token = await run_in_threadpool(
            AuthService(db).login,
            payload.username,
            payload.password,
            request.cookies.get(settings.session_cookie_name),
        )
        response = response_json(public)
        response.set_cookie(
            settings.session_cookie_name,
            token,
            max_age=43200,
            path="/",
            httponly=True,
            secure=settings.auth_secure_cookie,
            samesite="lax",
        )
        return response
    except AuthError as error:
        return failure(error, request)
    except SQLAlchemyError:
        db.rollback()
        return response_json({"detail": "Serviço temporariamente indisponível"}, 503)


async def require_auth(request: Request, db: Database):
    try:
        return await run_in_threadpool(
            AuthService(db).current_session,
            request.cookies.get(request.app.state.settings.session_cookie_name),
        )
    except AuthError:
        raise


@router.get("/session")
async def current_session(request: Request, db: Database):
    try:
        return response_json(await require_auth(request, db))
    except AuthError as error:
        return failure(error, request)
    except SQLAlchemyError:
        db.rollback()
        return response_json({"detail": "Serviço temporariamente indisponível"}, 503)


@router.post("/logout")
async def logout(request: Request, db: Database):
    try:
        guard_write(request)
        await limited_body(request)
        await run_in_threadpool(
            AuthService(db).logout,
            request.cookies.get(request.app.state.settings.session_cookie_name),
        )
        response = Response(status_code=204, headers={"Cache-Control": "no-store"})
        clear_cookie(response, request.app.state.settings)
        return response
    except AuthError as error:
        return failure(error, request)
    except SQLAlchemyError:
        db.rollback()
        return response_json({"detail": "Serviço temporariamente indisponível"}, 503)
