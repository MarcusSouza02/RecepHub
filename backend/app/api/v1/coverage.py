import json
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, guard_write, limited_body, require_auth, response_json
from app.schemas.coverage import CoverageConfirm, CoveragePreview
from app.services.auth import AuthError
from app.services.coverage import CoverageService

router = APIRouter(prefix="/schedules", tags=["coverage"], dependencies=[Depends(require_auth)])


async def write(schedule_id, request, db, schema, method):
    guard_write(request)
    try:
        payload = schema.model_validate(json.loads(await limited_body(request)))
        content = await run_in_threadpool(
            getattr(CoverageService(db), method), schedule_id, payload
        )
    except (ValidationError, ValueError, UnicodeDecodeError):
        db.rollback()
        raise AuthError(422, "Dados de cobertura inválidos") from None
    return response_json(content)


@router.post("/{schedule_id}/coverage/preview")
async def preview(schedule_id: UUID, request: Request, db: Database):
    return await write(schedule_id, request, db, CoveragePreview, "preview")


@router.post("/{schedule_id}/coverage/confirm")
async def confirm(schedule_id: UUID, request: Request, db: Database):
    return await write(schedule_id, request, db, CoverageConfirm, "confirm")
