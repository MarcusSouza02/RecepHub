import json
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, guard_write, limited_body, require_auth, response_json
from app.schemas.exports import ExportInput
from app.services.auth import AuthError
from app.services.exports import ExportService

router = APIRouter(prefix="/schedules", tags=["exports"], dependencies=[Depends(require_auth)])


async def export_input(request):
    guard_write(request)
    body = await limited_body(request)
    try:
        return ExportInput.model_validate(json.loads(body))
    except (ValidationError, ValueError, UnicodeDecodeError):
        raise AuthError(422, "Opções de exportação inválidas") from None


@router.post("/{schedule_id}/exports/preview")
async def preview_export(schedule_id: UUID, request: Request, db: Database):
    payload = await export_input(request)
    metadata = await run_in_threadpool(ExportService(db).preview, schedule_id, payload)
    return response_json(metadata)


@router.post("/{schedule_id}/exports")
async def generate_export(schedule_id: UUID, request: Request, db: Database):
    payload = await export_input(request)
    metadata, content = await run_in_threadpool(ExportService(db).generate, schedule_id, payload)
    return Response(
        content,
        media_type="application/pdf" if payload.format == "pdf" else "image/png",
        headers={
            "Content-Disposition": f'attachment; filename="{metadata["filename"]}"',
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
        },
    )
