import json

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, guard_write, limited_body, require_auth, response_json
from app.schemas.communications import CommunicationPrepare
from app.services.auth import AuthError
from app.services.communications import CommunicationService

router = APIRouter(
    prefix="/communications", tags=["communications"], dependencies=[Depends(require_auth)]
)


@router.post("/prepare")
async def prepare(request: Request, db: Database):
    guard_write(request)
    try:
        payload = CommunicationPrepare.model_validate(json.loads(await limited_body(request)))
    except (ValidationError, ValueError, UnicodeDecodeError):
        raise AuthError(422, "Dados do comunicado inválidos") from None
    return response_json(await run_in_threadpool(CommunicationService(db).prepare, payload))
