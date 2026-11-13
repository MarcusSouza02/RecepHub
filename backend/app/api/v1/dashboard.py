from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool

from app.api.v1.auth import Database, require_auth, response_json
from app.models.employee import Employee
from app.models.unit import Unit

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
Authenticated = Annotated[dict, Depends(require_auth)]


def operational_summary(db):
    # One statement keeps the three counters in the same PostgreSQL snapshot.
    statement = select(
        select(func.count()).select_from(Unit).where(Unit.active.is_(True)).scalar_subquery(),
        select(func.count())
        .select_from(Employee)
        .where(Employee.active.is_(True))
        .scalar_subquery(),
        select(func.count())
        .select_from(Employee)
        .where(Employee.active.is_(True), Employee.home_unit_id.is_(None))
        .scalar_subquery(),
    )
    units, employees, unassigned = db.execute(statement).one()
    return {
        "active_units": units,
        "active_employees": employees,
        "active_employees_without_home_unit": unassigned,
    }


@router.get("/summary")
async def summary(db: Database, authenticated: Authenticated):
    return response_json(await run_in_threadpool(operational_summary, db))
