from datetime import timedelta

from pydantic import ValidationError
from sqlalchemy import select

from app.models.employee import Employee
from app.models.schedule import ScheduleAssignment
from app.models.unit import Unit
from app.schemas.work_patterns import WorkPatternDay
from app.services.absence_conflicts import (
    absence_intersects,
    active_absences,
    work_segments,
)
from app.services.auth import AuthError
from app.services.schedules import ScheduleService


class CoverageService:
    def __init__(self, db):
        self.db = db
        self.schedules = ScheduleService(db)

    def candidate(self, employee, day, assignments, absences, unit, payload):
        reasons = []
        known = []
        unavailable = False
        insufficient = False

        def reason(code, message, *, unknown=False):
            nonlocal unavailable, insufficient
            reasons.append({"code": code, "message": message})
            insufficient |= unknown
            unavailable |= not unknown

        if not employee.active:
            reason("inactive_employee", "Colaboradora inativa")
        if unit is None or not unit.active:
            reason("inactive_unit", "Destino indisponível ou inativo")
        if day is None:
            reason("missing_day", "Colaboradora ausente da semana congelada", unknown=True)
        else:
            if day.state in ("excluded", "non_working"):
                reason("non_working_day", "Dia explicitamente sem trabalho ou excluído")
            try:
                source = WorkPatternDay.model_validate(
                    {
                        key: day.source_data.get(key)
                        for key in (
                            "weekday",
                            "state",
                            "start_time",
                            "end_time",
                            "break_start_time",
                            "break_end_time",
                        )
                    }
                )
            except (ValidationError, TypeError):
                source = None
            if source is None or source.state == "pending" or not source.is_complete:
                reason("unknown_pattern", "Horário congelado incompleto", unknown=True)
            elif source.state == "non_working":
                reason("non_working_pattern", "Horário congelado sem trabalho")
            else:
                known = work_segments(
                    source.start_time,
                    source.end_time,
                    source.break_start_time,
                    source.break_end_time,
                )
                if not any(a <= payload.start_time and payload.end_time <= b for a, b in known):
                    reason("outside_pattern", "Período fora da jornada conhecida")

                def minutes(segments):
                    return sum(
                        (b.hour * 60 + b.minute) - (a.hour * 60 + a.minute) for a, b in segments
                    )

                assigned_minutes = sum(
                    minutes(
                        work_segments(
                            assignment.start_time,
                            assignment.end_time,
                            getattr(assignment, "break_start_time", None),
                            getattr(assignment, "break_end_time", None),
                        )
                    )
                    for assignment in assignments
                )
                if assigned_minutes + minutes([(payload.start_time, payload.end_time)]) > minutes(
                    known
                ):
                    reason(
                        "exceeds_known_duration", "A soma dos períodos excede a duração conhecida"
                    )
            if any(
                assignment.start_time < payload.end_time
                and payload.start_time < assignment.end_time
                for assignment in assignments
            ):
                reason("assignment_overlap", "Já existe alocação neste período")
        if any(
            absence.employee_id == employee.id
            and absence_intersects(
                absence, payload.work_date, [(payload.start_time, payload.end_time)]
            )
            for absence in absences
        ):
            reason("absence_conflict", "Existe ausência ativa neste período")
        return {
            "employee_id": employee.id,
            "employee_name": day.employee_name_snapshot if day else employee.display_name,
            "classification": (
                "unavailable"
                if unavailable
                else "insufficient_information"
                if insufficient
                else "available"
            ),
            "reasons": reasons,
            "known_periods": [{"start_time": a, "end_time": b} for a, b in known],
        }

    @staticmethod
    def check_date(schedule, payload):
        if not schedule.week_start <= payload.work_date <= schedule.week_start + timedelta(days=6):
            raise AuthError(422, "A data deve pertencer à semana selecionada")

    def preview(self, schedule_id, payload):
        schedule = self.schedules.get(schedule_id, payload.expected_version)
        self.check_date(schedule, payload)
        employees = self.db.scalars(
            select(Employee).order_by(Employee.display_name, Employee.id)
        ).all()
        unit = self.db.get(Unit, payload.unit_id)
        days, assignments = self.schedules.rows(schedule_id)
        by_employee = {day.employee_id: day for day in days if day.work_date == payload.work_date}
        absences = active_absences(
            self.db,
            [employee.id for employee in employees],
            payload.work_date,
            payload.work_date,
        )
        return {
            "schedule_id": schedule.id,
            "expected_version": schedule.version,
            "request": payload.model_dump(exclude={"employee_id", "confirmed"}),
            "candidates": [
                self.candidate(
                    employee,
                    by_employee.get(employee.id),
                    assignments.get(by_employee[employee.id].id, [])
                    if employee.id in by_employee
                    else [],
                    absences,
                    unit,
                    payload,
                )
                for employee in employees
            ],
        }

    def confirm(self, schedule_id, payload):
        schedule = self.schedules.get(schedule_id, payload.expected_version)
        self.check_date(schedule, payload)
        employee = self.db.scalar(
            select(Employee)
            .where(Employee.id == payload.employee_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if employee is None:
            raise AuthError(404, "Colaboradora não encontrada")
        unit = self.db.scalar(
            select(Unit)
            .where(Unit.id == payload.unit_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        days, assignments = self.schedules.rows(schedule_id)
        day = next(
            (
                day
                for day in days
                if day.employee_id == employee.id and day.work_date == payload.work_date
            ),
            None,
        )
        absences = active_absences(self.db, [employee.id], payload.work_date, payload.work_date)
        candidate = self.candidate(
            employee,
            day,
            assignments.get(day.id, []) if day else [],
            absences,
            unit,
            payload,
        )
        if candidate["classification"] != "available":
            raise AuthError(409, "A cobertura não está disponível; consulte os impedimentos")
        self.db.add(
            ScheduleAssignment(
                day_id=day.id,
                unit_id=unit.id,
                unit_name_snapshot=unit.name,
                start_time=payload.start_time,
                end_time=payload.end_time,
                position=payload.position,
            )
        )
        day.state = "working"
        return self.schedules.finish(schedule)
