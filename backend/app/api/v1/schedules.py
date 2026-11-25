import json
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, guard_write, limited_body, require_auth, response_json
from app.schemas.schedules import (
    AssignmentCreate,
    AssignmentPatch,
    DayPatch,
    PublishInput,
    ScheduleCreate,
    ScheduleQuery,
    VersionInput,
)
from app.services.auth import AuthError
from app.services.schedules import ScheduleService

router = APIRouter(prefix="/schedules", tags=["schedules"], dependencies=[Depends(require_auth)])


async def write(request, db, schema, method, *args, status=200):
    guard_write(request)
    body = await limited_body(request)
    try:
        payload = schema.model_validate(json.loads(body))
        content = await run_in_threadpool(getattr(ScheduleService(db), method), *args, payload)
    except (ValidationError, ValueError, UnicodeDecodeError):
        db.rollback()
        raise AuthError(422, "Dados da escala inválidos") from None
    return response_json(content, status)


@router.get("")
def list_schedules(request: Request, db: Database):
    try:
        if len(request.query_params.multi_items()) != len(set(request.query_params.keys())):
            raise ValueError("Parâmetro repetido")
        filters = ScheduleQuery.model_validate(dict(request.query_params))
    except (ValidationError, ValueError):
        raise AuthError(422, "Filtros de escalas inválidos") from None
    return response_json(ScheduleService(db).list(filters))


@router.post("", status_code=201)
async def create_schedule(request: Request, db: Database):
    return await write(request, db, ScheduleCreate, "create", status=201)


@router.get("/{schedule_id}")
def get_schedule(schedule_id: UUID, db: Database):
    return response_json(ScheduleService(db).detail(schedule_id))


@router.post("/{schedule_id}/assignments")
async def add_assignment(schedule_id: UUID, request: Request, db: Database):
    return await write(request, db, AssignmentCreate, "add_assignment", schedule_id)


@router.patch("/{schedule_id}/assignments/{assignment_id}")
async def patch_assignment(schedule_id: UUID, assignment_id: UUID, request: Request, db: Database):
    return await write(request, db, AssignmentPatch, "patch_assignment", schedule_id, assignment_id)


@router.post("/{schedule_id}/assignments/{assignment_id}/remove")
async def remove_assignment(schedule_id: UUID, assignment_id: UUID, request: Request, db: Database):
    return await write(request, db, VersionInput, "remove_assignment", schedule_id, assignment_id)


@router.patch("/{schedule_id}/days/{day_id}")
async def patch_day(schedule_id: UUID, day_id: UUID, request: Request, db: Database):
    return await write(request, db, DayPatch, "patch_day", schedule_id, day_id)


@router.post("/{schedule_id}/validate")
async def validate_schedule(schedule_id: UUID, request: Request, db: Database):
    return await write(request, db, VersionInput, "validate", schedule_id)


@router.post("/{schedule_id}/publish")
async def publish_schedule(schedule_id: UUID, request: Request, db: Database):
    return await write(request, db, PublishInput, "publish", schedule_id, status=201)


@router.get("/{schedule_id}/revisions")
def revisions(schedule_id: UUID, db: Database):
    return response_json(ScheduleService(db).revisions(schedule_id))


@router.get("/{schedule_id}/revisions/{number}")
def revision(schedule_id: UUID, number: int, db: Database):
    return response_json(ScheduleService(db).revision(schedule_id, number))
