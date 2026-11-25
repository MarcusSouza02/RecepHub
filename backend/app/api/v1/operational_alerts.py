from datetime import date

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from sqlalchemy import and_, exists, func, or_, select

from app.api.v1.auth import Database, require_auth, response_json
from app.models.absence import Absence
from app.models.employee import Employee
from app.models.schedule import ScheduleAssignment, ScheduleEmployeeDay
from app.services.auth import AuthError

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_auth)])


class AlertPeriod(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_date: date
    to_date: date

    @model_validator(mode="after")
    def bounded_period(self):
        if not 0 <= (self.to_date - self.from_date).days <= 30:
            raise ValueError("Selecione até 31 dias consecutivos")
        return self


def operational_alerts(db, period):
    absence_filter = (
        Absence.status == "active",
        Absence.start_date <= period.to_date,
        Absence.end_date >= period.from_date,
    )
    absence_total = db.scalar(select(func.count()).select_from(Absence).where(*absence_filter))
    absence_rows = db.execute(
        select(Absence, Employee.display_name)
        .join(Employee, Employee.id == Absence.employee_id)
        .where(*absence_filter)
        .order_by(Absence.start_date, Absence.id)
        .limit(20)
    ).all()
    # EXISTS counts each affected assignment once even when absences overlap.
    left_end = func.coalesce(ScheduleAssignment.break_start_time, ScheduleAssignment.end_time)
    right_start = func.coalesce(ScheduleAssignment.break_end_time, ScheduleAssignment.end_time)
    partial_overlap = or_(
        and_(
            ScheduleAssignment.start_time < left_end,
            ScheduleAssignment.start_time < Absence.end_time,
            Absence.start_time < left_end,
        ),
        and_(
            right_start < ScheduleAssignment.end_time,
            right_start < Absence.end_time,
            Absence.start_time < ScheduleAssignment.end_time,
        ),
    )
    absence_conditions = (
        Absence.employee_id == ScheduleEmployeeDay.employee_id,
        Absence.status == "active",
        Absence.start_date <= ScheduleEmployeeDay.work_date,
        Absence.end_date >= ScheduleEmployeeDay.work_date,
        or_(
            and_(
                Absence.mode == "full_day",
                or_(
                    ScheduleAssignment.start_time < left_end,
                    right_start < ScheduleAssignment.end_time,
                ),
            ),
            partial_overlap,
        ),
    )
    conflict = exists(select(Absence.id).where(*absence_conditions))
    absence_ids = (
        select(func.array_agg(Absence.id))
        .where(*absence_conditions)
        .correlate(
            ScheduleAssignment,
            ScheduleEmployeeDay,
        )
        .scalar_subquery()
    )
    query = (
        select(ScheduleAssignment, ScheduleEmployeeDay, absence_ids.label("absence_ids"))
        .join(
            ScheduleEmployeeDay,
            ScheduleAssignment.day_id == ScheduleEmployeeDay.id,
        )
        .where(
            ScheduleEmployeeDay.work_date >= period.from_date,
            ScheduleEmployeeDay.work_date <= period.to_date,
            conflict,
        )
    )
    conflict_total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(
        query.order_by(
            ScheduleEmployeeDay.work_date,
            ScheduleEmployeeDay.schedule_id,
            ScheduleAssignment.id,
        ).limit(20)
    ).all()
    return {
        "from_date": period.from_date,
        "to_date": period.to_date,
        "active_absences": {
            "total": absence_total,
            "truncated": absence_total > 20,
            "items": [
                {
                    "id": absence.id,
                    "employee_name": name,
                    "type": absence.type,
                    "start_date": absence.start_date,
                    "end_date": absence.end_date,
                    "href": f"/absences/{absence.id}",
                }
                for absence, name in absence_rows
            ],
        },
        "current_assignment_conflicts": {
            "total": conflict_total,
            "truncated": conflict_total > 20,
            "items": [
                {
                    "schedule_id": day.schedule_id,
                    "assignment_id": assignment.id,
                    "employee_name": day.employee_name_snapshot,
                    "work_date": day.work_date,
                    "absence_ids": identifiers,
                    "href": f"/schedules/{day.schedule_id}",
                }
                for assignment, day, identifiers in rows
            ],
        },
    }


@router.get("/operational-alerts")
def alerts(request: Request, db: Database):
    try:
        if len(request.query_params.multi_items()) != len(set(request.query_params.keys())):
            raise ValueError("Parâmetro repetido")
        period = AlertPeriod.model_validate(dict(request.query_params))
    except (ValidationError, ValueError):
        raise AuthError(422, "Informe um período válido de até 31 dias") from None
    return response_json(operational_alerts(db, period))
