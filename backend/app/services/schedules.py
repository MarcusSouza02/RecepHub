from datetime import date, timedelta

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.models.schedule import Schedule, ScheduleAssignment, ScheduleEmployeeDay, ScheduleRevision
from app.models.unit import Unit
from app.schemas.schedules import AssignmentTimes
from app.schemas.work_patterns import WorkPatternDay
from app.services.auth import AuthError

TIME_FIELDS = ("start_time", "end_time", "break_start_time", "break_end_time")


class ScheduleService:
    def __init__(self, db):
        self.db = db

    def get(self, schedule_id, version=None):
        query = select(Schedule).where(Schedule.id == schedule_id)
        if version is not None:
            query = query.with_for_update()
        else:
            query = query.with_for_update(read=True)
        schedule = self.db.scalar(query.execution_options(populate_existing=True))
        if schedule is None:
            raise AuthError(404, "Escala não encontrada")
        if version is not None and schedule.version != version:
            raise AuthError(409, "A escala foi alterada; recarregue antes de continuar")
        return schedule

    def list(self, filters):
        conditions = []
        if filters.from_date:
            first = date.fromordinal(max(date.min.toordinal(), filters.from_date.toordinal() - 6))
            conditions.append(Schedule.week_start >= first)
        if filters.to_date:
            conditions.append(Schedule.week_start <= filters.to_date)
        total = self.db.scalar(select(func.count()).select_from(Schedule).where(*conditions))
        rows = self.db.scalars(
            select(Schedule)
            .where(*conditions)
            .order_by(Schedule.week_start.desc(), Schedule.id)
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        ).all()
        return {
            "items": [self.summary(row) for row in rows],
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
        }

    @staticmethod
    def summary(schedule):
        return {
            key: getattr(schedule, key)
            for key in (
                "id",
                "week_start",
                "status",
                "version",
                "latest_revision_number",
                "created_at",
                "updated_at",
            )
        }

    def rows(self, schedule_id):
        days = self.db.scalars(
            select(ScheduleEmployeeDay)
            .where(ScheduleEmployeeDay.schedule_id == schedule_id)
            .order_by(
                ScheduleEmployeeDay.work_date,
                ScheduleEmployeeDay.employee_name_snapshot,
                ScheduleEmployeeDay.employee_id,
            )
        ).all()
        assignments = self.db.scalars(
            select(ScheduleAssignment)
            .join(ScheduleEmployeeDay, ScheduleAssignment.day_id == ScheduleEmployeeDay.id)
            .where(ScheduleEmployeeDay.schedule_id == schedule_id)
            .order_by(ScheduleAssignment.start_time, ScheduleAssignment.id)
        ).all()
        grouped = {day.id: [] for day in days}
        for assignment in assignments:
            grouped[assignment.day_id].append(assignment)
        return days, grouped

    def diagnostics(self, schedule_id, *, lock=False):
        days, grouped = self.rows(schedule_id)
        employee_ids = sorted({day.employee_id for day in days})
        unit_ids = sorted({a.unit_id for rows in grouped.values() for a in rows})
        employee_query = select(Employee).where(Employee.id.in_(employee_ids)).order_by(Employee.id)
        unit_query = select(Unit).where(Unit.id.in_(unit_ids)).order_by(Unit.id)
        if lock:
            employee_query = employee_query.with_for_update()
            unit_query = unit_query.with_for_update()
        employees = {
            row.id: row
            for row in self.db.scalars(employee_query.execution_options(populate_existing=True))
        }
        units = {
            row.id: row
            for row in self.db.scalars(unit_query.execution_options(populate_existing=True))
        }
        errors = []

        def error(code, message, day, assignment=None):
            item = {"code": code, "message": message, "day_id": day.id}
            if assignment is not None:
                item["assignment_id"] = assignment.id
            errors.append(item)

        for day in days:
            rows = grouped[day.id]
            if day.state == "pending":
                error("pending_day", "Resolva a configuração pendente", day)
            if day.state == "working" and not rows:
                error("missing_assignment", "Dia de trabalho sem alocação", day)
            if rows and not employees.get(day.employee_id, None):
                error("missing_employee", "Colaboradora não encontrada", day)
            elif rows and not employees[day.employee_id].active:
                error("inactive_employee", "Colaboradora inativa requer resolução explícita", day)
            for index, assignment in enumerate(rows):
                unit = units.get(assignment.unit_id)
                if unit is None or not unit.active:
                    error("inactive_unit", "A alocação exige uma unidade ativa", day, assignment)
                if any(
                    other.start_time < assignment.end_time
                    and assignment.start_time < other.end_time
                    for other in rows[:index]
                ):
                    error(
                        "overlapping_assignment",
                        "Períodos da mesma pessoa se sobrepõem",
                        day,
                        assignment,
                    )
        return {"errors": errors, "warnings": []}

    def detail(self, schedule_id):
        schedule = self.get(schedule_id)
        days, grouped = self.rows(schedule_id)
        result = self.summary(schedule)
        result["days"] = [
            {
                "id": day.id,
                "employee_id": day.employee_id,
                "employee_name": day.employee_name_snapshot,
                "work_date": day.work_date,
                "state": day.state,
                "source_data": day.source_data,
                "resolution_note": day.resolution_note,
                "assignments": [
                    {
                        **{
                            key: getattr(row, key)
                            for key in ("id", "unit_id", *TIME_FIELDS, "position")
                        },
                        "unit_name": row.unit_name_snapshot,
                    }
                    for row in grouped[day.id]
                ],
            }
            for day in days
        ]
        result["diagnostics"] = self.diagnostics(schedule_id)
        return result

    def create(self, payload):
        if self.db.scalar(select(Schedule.id).where(Schedule.week_start == payload.week_start)):
            raise AuthError(409, "Já existe uma escala para esta semana")
        schedule = Schedule(
            week_start=payload.week_start, version=1, status="draft", latest_revision_number=0
        )
        self.db.add(schedule)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            raise AuthError(409, "Já existe uma escala para esta semana") from None
        employees = self.db.scalars(
            select(Employee)
            .where(Employee.active.is_(True))
            .order_by(Employee.id)
            .with_for_update()
        ).all()
        units = {
            row.id: row for row in self.db.scalars(select(Unit).order_by(Unit.id).with_for_update())
        }
        for employee in employees:
            patterns = {
                p.weekday: p
                for p in self.db.scalars(
                    select(EmployeeWorkPattern).where(
                        EmployeeWorkPattern.employee_id == employee.id
                    )
                )
            }
            for weekday in range(7):
                pattern = patterns.get(weekday)
                source = {
                    "weekday": weekday,
                    "state": pattern.state if pattern else "pending",
                    **{key: getattr(pattern, key, None) for key in TIME_FIELDS},
                }
                habitual = WorkPatternDay(**source)
                unit = units.get(employee.home_unit_id)
                ready = (
                    habitual.state == "working"
                    and habitual.is_complete
                    and unit is not None
                    and unit.active
                )
                state = (
                    "non_working"
                    if habitual.state == "non_working"
                    else "working"
                    if ready
                    else "pending"
                )
                source.update(
                    home_unit_id=employee.home_unit_id,
                    home_unit_name=unit.name if unit else None,
                    home_unit_active=unit.active if unit else None,
                )
                day = ScheduleEmployeeDay(
                    schedule_id=schedule.id,
                    employee_id=employee.id,
                    employee_name_snapshot=employee.display_name,
                    work_date=payload.week_start + timedelta(days=weekday),
                    state=state,
                    source_data=jsonable_encoder(source),
                )
                self.db.add(day)
                self.db.flush()
                if ready:
                    self.db.add(
                        ScheduleAssignment(
                            day_id=day.id,
                            unit_id=unit.id,
                            unit_name_snapshot=unit.name,
                            **{key: getattr(habitual, key) for key in TIME_FIELDS},
                        )
                    )
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise AuthError(409, "Já existe uma escala para esta semana") from None
        return self.detail(schedule.id)

    def day(self, schedule_id, day_id):
        day = self.db.scalar(
            select(ScheduleEmployeeDay).where(
                ScheduleEmployeeDay.id == day_id, ScheduleEmployeeDay.schedule_id == schedule_id
            )
        )
        if day is None:
            raise AuthError(404, "Dia não encontrado nesta escala")
        return day

    def assignment(self, schedule_id, assignment_id):
        row = self.db.scalar(
            select(ScheduleAssignment)
            .join(ScheduleEmployeeDay)
            .where(
                ScheduleAssignment.id == assignment_id,
                ScheduleEmployeeDay.schedule_id == schedule_id,
            )
        )
        if row is None:
            raise AuthError(404, "Alocação não encontrada nesta escala")
        return row

    def active_unit(self, unit_id):
        row = self.db.scalar(select(Unit).where(Unit.id == unit_id).with_for_update())
        if row is None:
            raise AuthError(404, "Unidade não encontrada")
        if not row.active:
            raise AuthError(409, "Selecione uma unidade ativa")
        return row

    def finish(self, schedule):
        self.db.flush()
        conflicts = [
            item
            for item in self.diagnostics(schedule.id)["errors"]
            if item["code"] == "overlapping_assignment"
        ]
        if conflicts:
            self.db.rollback()
            raise AuthError(409, "A colaboradora já possui alocação neste período")
        schedule.version += 1
        schedule.status = "draft"
        self.db.commit()
        return self.detail(schedule.id)

    def add_assignment(self, schedule_id, payload):
        schedule = self.get(schedule_id, payload.expected_version)
        day = self.day(schedule_id, payload.day_id)
        employee = self.db.scalar(
            select(Employee).where(Employee.id == day.employee_id).with_for_update()
        )
        if not employee.active:
            raise AuthError(409, "A colaboradora está inativa")
        unit = self.active_unit(payload.unit_id)
        values = payload.model_dump(exclude={"expected_version", "day_id"})
        self.db.add(ScheduleAssignment(day_id=day.id, unit_name_snapshot=unit.name, **values))
        day.state = "working"
        return self.finish(schedule)

    def patch_assignment(self, schedule_id, assignment_id, payload):
        schedule = self.get(schedule_id, payload.expected_version)
        row = self.assignment(schedule_id, assignment_id)
        values = payload.model_dump(exclude_unset=True, exclude={"expected_version"})
        AssignmentTimes(
            **{key: values.get(key, getattr(row, key)) for key in (*TIME_FIELDS, "position")}
        )
        if "unit_id" in values and values["unit_id"] != row.unit_id:
            row.unit_name_snapshot = self.active_unit(values["unit_id"]).name
        for key, value in values.items():
            setattr(row, key, value)
        return self.finish(schedule)

    def remove_assignment(self, schedule_id, assignment_id, payload):
        schedule = self.get(schedule_id, payload.expected_version)
        self.db.delete(self.assignment(schedule_id, assignment_id))
        return self.finish(schedule)

    def patch_day(self, schedule_id, day_id, payload):
        schedule = self.get(schedule_id, payload.expected_version)
        day = self.day(schedule_id, day_id)
        if payload.state != "working" and self.db.scalar(
            select(ScheduleAssignment.id).where(ScheduleAssignment.day_id == day.id).limit(1)
        ):
            raise AuthError(409, "Remova as alocações antes de alterar o estado do dia")
        day.state = payload.state
        day.resolution_note = payload.resolution_note
        return self.finish(schedule)

    def validate(self, schedule_id, payload):
        self.get(schedule_id, payload.expected_version)
        return self.diagnostics(schedule_id, lock=True)

    def publish(self, schedule_id, payload):
        schedule = self.get(schedule_id, payload.expected_version)
        diagnostics = self.diagnostics(schedule_id, lock=True)
        if diagnostics["errors"]:
            raise AuthError(409, "Resolva os impedimentos antes de publicar")
        snapshot = jsonable_encoder(self.detail(schedule_id))
        snapshot.update(
            status="published",
            latest_revision_number=schedule.latest_revision_number + 1,
            source_version=schedule.version,
        )
        revision = ScheduleRevision(
            schedule_id=schedule.id,
            number=schedule.latest_revision_number + 1,
            source_version=schedule.version,
            schema_version=1,
            snapshot=snapshot,
        )
        self.db.add(revision)
        schedule.latest_revision_number += 1
        schedule.version += 1
        schedule.status = "published"
        self.db.commit()
        self.db.refresh(revision)
        return self.revision_data(revision)

    @staticmethod
    def revision_data(revision):
        return {
            key: getattr(revision, key)
            for key in (
                "id",
                "number",
                "source_version",
                "schema_version",
                "published_at",
                "snapshot",
            )
        }

    def revisions(self, schedule_id):
        self.get(schedule_id)
        rows = self.db.scalars(
            select(ScheduleRevision)
            .where(ScheduleRevision.schedule_id == schedule_id)
            .order_by(ScheduleRevision.number.desc())
        ).all()
        return {"items": [self.revision_data(row) for row in rows]}

    def revision(self, schedule_id, number):
        self.get(schedule_id)
        row = self.db.scalar(
            select(ScheduleRevision).where(
                ScheduleRevision.schedule_id == schedule_id, ScheduleRevision.number == number
            )
        )
        if row is None:
            raise AuthError(404, "Revisão não encontrada")
        return self.revision_data(row)
