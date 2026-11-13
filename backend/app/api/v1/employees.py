import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, guard_write, limited_body, require_auth, response_json
from app.schemas.employees import EmployeeCreate, EmployeePatch, EmployeeQuery
from app.services.auth import AuthError
from app.services.employees import EmployeeService, representation

router = APIRouter(tags=["employees"], dependencies=[Depends(require_auth)])


async def read_payload(request, schema):
    guard_write(request)
    body = await limited_body(request)
    try:
        return schema.model_validate(json.loads(body))
    except (ValidationError, ValueError, UnicodeDecodeError):
        raise AuthError(422, "Dados da colaboradora inválidos") from None


def query_filters(request: Request):
    try:
        return EmployeeQuery.model_validate(dict(request.query_params))
    except ValidationError:
        raise AuthError(422, "Filtros de colaboradoras inválidos") from None


Filters = Annotated[EmployeeQuery, Depends(query_filters)]


@router.get("/employees")
def list_employees(db: Database, filters: Filters):
    return response_json(EmployeeService(db).list(filters))


@router.post("/employees", status_code=201)
async def create_employee(request: Request, db: Database):
    payload = await read_payload(request, EmployeeCreate)
    return response_json(await run_in_threadpool(EmployeeService(db).create, payload), 201)


@router.get("/employees/{employee_id}")
def get_employee(employee_id: UUID, db: Database):
    return response_json(representation(EmployeeService(db).get(employee_id)))


@router.patch("/employees/{employee_id}")
async def patch_employee(employee_id: UUID, request: Request, db: Database):
    payload = await read_payload(request, EmployeePatch)
    return response_json(await run_in_threadpool(EmployeeService(db).patch, employee_id, payload))


@router.get("/units/{unit_id}/employees")
def list_unit_employees(unit_id: UUID, request: Request, db: Database):
    filters = query_filters(request)
    if filters.without_home_unit or (
        filters.home_unit_id is not None and filters.home_unit_id != unit_id
    ):
        raise AuthError(422, "Filtro incompatível com a unidade da rota")
    service = EmployeeService(db)
    service.require_unit(unit_id)
    return response_json(service.list(filters.model_copy(update={"home_unit_id": unit_id})))
