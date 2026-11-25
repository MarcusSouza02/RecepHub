from datetime import date, time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.v1.auth import require_auth
from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.models.schedule import Schedule, ScheduleAssignment, ScheduleRevision
from app.models.unit import Unit
from app.schemas.schedules import AssignmentPatch, PublishInput, ScheduleCreate
from app.services.auth import AuthError
from app.services.schedules import ScheduleService

HEADERS = {"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"}
URL = "/api/v1/schedules"
IDENTIFIER = str(uuid4())


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", ""),
        ("post", ""),
        ("get", f"/{IDENTIFIER}"),
        ("post", f"/{IDENTIFIER}/assignments"),
        ("patch", f"/{IDENTIFIER}/assignments/{IDENTIFIER}"),
        ("post", f"/{IDENTIFIER}/assignments/{IDENTIFIER}/remove"),
        ("patch", f"/{IDENTIFIER}/days/{IDENTIFIER}"),
        ("post", f"/{IDENTIFIER}/validate"),
        ("post", f"/{IDENTIFIER}/publish"),
        ("get", f"/{IDENTIFIER}/revisions"),
        ("get", f"/{IDENTIFIER}/revisions/1"),
    ],
)
def test_every_schedule_endpoint_requires_session(client, method, path):
    response = getattr(client, method)(URL + path)
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


@pytest.fixture
def safety_client():
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", ""),
        ("post", f"/{IDENTIFIER}/assignments"),
        ("patch", f"/{IDENTIFIER}/assignments/{IDENTIFIER}"),
        ("post", f"/{IDENTIFIER}/assignments/{IDENTIFIER}/remove"),
        ("patch", f"/{IDENTIFIER}/days/{IDENTIFIER}"),
        ("post", f"/{IDENTIFIER}/validate"),
        ("post", f"/{IDENTIFIER}/publish"),
    ],
)
def test_schedule_writes_reject_missing_csrf(safety_client, method, path):
    response = getattr(safety_client, method)(URL + path, json={})
    assert response.status_code == 403


def test_schedule_uuid_errors_do_not_echo_input(safety_client):
    private_input = "fictional-private-person-name"
    response = safety_client.get(f"{URL}/{private_input}")
    assert response.status_code == 422
    assert private_input not in response.text
    assert response.headers["cache-control"] == "no-store"


@pytest.fixture
def ready_schedule(db_session):
    unit = Unit(name="Unidade original ficticia")
    db_session.add(unit)
    db_session.flush()
    employee = Employee(display_name="Pessoa original ficticia", home_unit_id=unit.id)
    db_session.add(employee)
    db_session.flush()
    for weekday in range(7):
        db_session.add(
            EmployeeWorkPattern(
                employee_id=employee.id,
                weekday=weekday,
                state="working" if weekday == 0 else "non_working",
                start_time=time(8) if weekday == 0 else None,
                end_time=time(16) if weekday == 0 else None,
            )
        )
    db_session.commit()
    service = ScheduleService(db_session)
    detail = service.create(ScheduleCreate(week_start=date(2026, 11, 23)))
    return service, detail, employee, unit


@pytest.mark.integration
def test_assignment_and_day_identifiers_cannot_cross_schedules(ready_schedule):
    service, detail, _, _ = ready_schedule
    other = service.create(ScheduleCreate(week_start=date(2026, 11, 30)))
    day = detail["days"][0]
    assignment = day["assignments"][0]
    for lookup, identifier in ((service.day, day["id"]), (service.assignment, assignment["id"])):
        with pytest.raises(AuthError) as error:
            lookup(other["id"], identifier)
        assert error.value.status == 404
    assert service.detail(detail["id"])["version"] == 1
    assert service.detail(other["id"])["version"] == 1


@pytest.mark.integration
def test_published_snapshot_survives_renaming_and_second_revision(ready_schedule):
    service, detail, employee, unit = ready_schedule
    first = service.publish(detail["id"], PublishInput(expected_version=1, confirmed=True))
    frozen = first["snapshot"]
    employee.display_name = "Pessoa renomeada ficticia"
    unit.name = "Unidade renomeada ficticia"
    service.db.commit()
    assignment_id = detail["days"][0]["assignments"][0]["id"]
    edited = service.patch_assignment(
        detail["id"], assignment_id, AssignmentPatch(expected_version=2, position="Atividade nova")
    )
    second = service.publish(
        detail["id"], PublishInput(expected_version=edited["version"], confirmed=True)
    )
    assert second["number"] == 2
    assert service.revision(detail["id"], 1)["snapshot"] == frozen
    day = frozen["days"][0]
    assert day["employee_name"] == "Pessoa original ficticia"
    assert day["assignments"][0]["unit_name"] == "Unidade original ficticia"
    assert day["assignments"][0]["position"] is None
    assert second["snapshot"]["days"][0]["assignments"][0]["position"] == "Atividade nova"


@pytest.mark.integration
def test_stale_edit_and_repeated_publication_do_not_change_published_data(ready_schedule):
    service, detail, _, _ = ready_schedule
    first = service.publish(detail["id"], PublishInput(expected_version=1, confirmed=True))
    assignment_id = detail["days"][0]["assignments"][0]["id"]
    for operation in (
        lambda: service.publish(detail["id"], PublishInput(expected_version=1, confirmed=True)),
        lambda: service.patch_assignment(
            detail["id"],
            assignment_id,
            AssignmentPatch(expected_version=1, position="Edicao obsoleta"),
        ),
    ):
        with pytest.raises(AuthError) as error:
            operation()
        assert error.value.status == 409
    assert service.detail(detail["id"])["version"] == 2
    assert len(service.revisions(detail["id"])["items"]) == 1
    assert service.revision(detail["id"], 1)["snapshot"] == first["snapshot"]


@pytest.mark.integration
def test_publish_commit_failure_rolls_back_revision_and_version(ready_schedule, monkeypatch):
    service, detail, _, _ = ready_schedule
    app = create_app(Settings(_env_file=None))
    app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}

    def session_dependency():
        with Session(bind=service.db.bind, join_transaction_mode="create_savepoint") as session:

            def failing_commit():
                session.flush()
                raise OperationalError("fictional-secret-sql", {}, Exception("private"))

            monkeypatch.setattr(session, "commit", failing_commit)
            yield session

    app.dependency_overrides[get_session] = session_dependency
    with TestClient(app) as client:
        response = client.post(
            f"{URL}/{detail['id']}/publish",
            headers=HEADERS,
            json={"expected_version": 1, "confirmed": True},
        )
    assert response.status_code == 503
    assert "fictional-secret-sql" not in response.text
    assert "private" not in response.text
    service.db.expire_all()
    schedule = service.db.get(Schedule, detail["id"])
    assert (schedule.version, schedule.latest_revision_number, schedule.status) == (1, 0, "draft")
    assert service.db.scalar(select(func.count()).select_from(ScheduleRevision)) == 0
    assert service.db.scalar(select(func.count()).select_from(ScheduleAssignment)) == 1
