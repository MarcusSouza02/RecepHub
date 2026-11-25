import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, guard_write, limited_body, require_auth, response_json
from app.schemas.absences import AbsenceCancel, AbsenceCreate, AbsencePatch, AbsenceQuery
from app.services.absences import AbsenceService
from app.services.auth import AuthError

router = APIRouter(tags=["absences"], dependencies=[Depends(require_auth)])


async def read_payload(request, schema):
    guard_write(request)
    body = await limited_body(request)
    try:
        return schema.model_validate(json.loads(body))
    except (ValidationError, ValueError, UnicodeDecodeError):
        raise AuthError(422, "Dados da ausência inválidos") from None


def query_filters(request: Request):
    try:
        keys = list(request.query_params.keys())
        if any(len(request.query_params.getlist(key)) != 1 for key in keys):
            raise ValueError("Parâmetro repetido")
        return AbsenceQuery.model_validate(dict(request.query_params))
    except (ValidationError, ValueError):
        raise AuthError(422, "Filtros de ausências inválidos") from None


Filters = Annotated[AbsenceQuery, Depends(query_filters)]


@router.get("/absences")
def list_absences(db: Database, filters: Filters):
    return response_json(AbsenceService(db).list(filters))


@router.post("/absences", status_code=201)
async def create_absence(request: Request, db: Database):
    payload = await read_payload(request, AbsenceCreate)
    return response_json(await run_in_threadpool(AbsenceService(db).create, payload), 201)


@router.get("/absences/{absence_id}")
def get_absence(absence_id: UUID, db: Database):
    return response_json(AbsenceService(db).detail(absence_id))


@router.patch("/absences/{absence_id}")
async def patch_absence(absence_id: UUID, request: Request, db: Database):
    payload = await read_payload(request, AbsencePatch)
    return response_json(await run_in_threadpool(AbsenceService(db).patch, absence_id, payload))


@router.post("/absences/{absence_id}/cancel")
async def cancel_absence(absence_id: UUID, request: Request, db: Database):
    payload = await read_payload(request, AbsenceCancel)
    return response_json(await run_in_threadpool(AbsenceService(db).cancel, absence_id, payload))


@router.get("/absences/{absence_id}/events")
def get_events(absence_id: UUID, db: Database):
    return response_json(AbsenceService(db).events(absence_id))
