import json
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, guard_write, limited_body, require_auth, response_json
from app.schemas.work_patterns import WorkPatternPut
from app.services.auth import AuthError
from app.services.work_patterns import WorkPatternService

router = APIRouter(tags=["work-patterns"], dependencies=[Depends(require_auth)])


@router.get("/employees/{employee_id}/work-patterns")
def get_work_patterns(employee_id: UUID, db: Database):
    return response_json(WorkPatternService(db).get(employee_id))


@router.put("/employees/{employee_id}/work-patterns")
async def put_work_patterns(employee_id: UUID, request: Request, db: Database):
    guard_write(request)
    body = await limited_body(request)
    try:
        payload = WorkPatternPut.model_validate(json.loads(body))
    except (ValidationError, ValueError, UnicodeDecodeError):
        raise AuthError(422, "Horários habituais inválidos") from None
    return response_json(await run_in_threadpool(WorkPatternService(db).put, employee_id, payload))
