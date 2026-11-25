from sqlalchemy import select

from app.models.absence import Absence


def work_segments(start, end, break_start=None, break_end=None):
    """Half-open intervals; an optional complete pause is not working time."""
    if break_start is not None and break_end is not None:
        return [(a, b) for a, b in ((start, break_start), (break_end, end)) if a < b]
    return [(start, end)]


def absence_intersects(absence, work_date, segments):
    if absence.status != "active" or not absence.start_date <= work_date <= absence.end_date:
        return False
    if absence.mode == "full_day":
        return bool(segments)
    return any(a < absence.end_time and absence.start_time < b for a, b in segments)


def active_absences(db, employee_ids, first_date, last_date):
    if not employee_ids:
        return []
    return db.scalars(
        select(Absence)
        .where(
            Absence.employee_id.in_(employee_ids),
            Absence.status == "active",
            Absence.start_date <= last_date,
            Absence.end_date >= first_date,
        )
        .order_by(Absence.id)
    ).all()


def absence_diagnostics(db, days, grouped_assignments):
    if not days:
        return {"errors": [], "warnings": []}
    absences = active_absences(
        db,
        {day.employee_id for day in days},
        min(day.work_date for day in days),
        max(day.work_date for day in days),
    )
    errors = []
    for day in days:
        for assignment in grouped_assignments.get(day.id, []):
            segments = work_segments(
                assignment.start_time,
                assignment.end_time,
                assignment.break_start_time,
                assignment.break_end_time,
            )
            identifiers = [
                absence.id
                for absence in absences
                if absence.employee_id == day.employee_id
                and absence_intersects(absence, day.work_date, segments)
            ]
            if identifiers:
                errors.append(
                    {
                        "code": "absence_conflict",
                        "message": "A alocação coincide com uma ausência ativa",
                        "day_id": day.id,
                        "assignment_id": assignment.id,
                        "absence_ids": identifiers,
                    }
                )
    return {"errors": errors, "warnings": []}
