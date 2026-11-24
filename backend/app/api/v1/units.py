import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, guard_write, limited_body, require_auth, response_json
from app.schemas.units import UnitCreate, UnitOutput, UnitPatch, UnitQuery
from app.services.auth import AuthError
from app.services.units import UnitService

router = APIRouter(prefix="/units", tags=["units"])
Authenticated = Annotated[dict, Depends(require_auth)]


def parse_id(value):
    try:
        return UUID(value)
    except ValueError:
        raise AuthError(422, "Identificador inválido") from None


async def payload(request, schema):
    guard_write(request)
    body = await limited_body(request)
    try:
        return schema.model_validate(json.loads(body))
    except (ValidationError, ValueError, UnicodeDecodeError):
        raise AuthError(422, "Dados de unidade inválidos") from None


@router.get("")
async def list_units(request: Request, db: Database, authenticated: Authenticated):
    try:
        query = UnitQuery.model_validate(dict(request.query_params))
    except ValidationError:
        raise AuthError(422, "Filtros inválidos") from None
    return response_json(await run_in_threadpool(UnitService(db).list, query))


@router.post("")
async def create_unit(request: Request, db: Database, authenticated: Authenticated):
    data = await payload(request, UnitCreate)
    return response_json(await run_in_threadpool(UnitService(db).create, data), 201)


@router.get("/{unit_id}")
async def get_unit(unit_id: str, db: Database, authenticated: Authenticated):
    unit = await run_in_threadpool(UnitService(db).get, parse_id(unit_id))
    return response_json(UnitOutput.model_validate(unit).model_dump())


@router.patch("/{unit_id}")
async def patch_unit(unit_id: str, request: Request, db: Database, authenticated: Authenticated):
    identifier = parse_id(unit_id)
    data = await payload(request, UnitPatch)
    return response_json(await run_in_threadpool(UnitService(db).patch, identifier, data))
