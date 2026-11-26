from datetime import date, time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app.api.v1.auth import require_auth
from app.core.config import Settings
from app.main import create_app
from app.models.absence import Absence
from app.models.employee import Employee
from app.models.employee_work_pattern import EmployeeWorkPattern
from app.models.schedule import ScheduleAssignment, ScheduleRevision
from app.models.unit import Unit
from app.schemas.proposals import Operation, ProposalConfirm, ProposalPreview
from app.schemas.schedules import ScheduleCreate
from app.services.ai.base import get_provider
from app.services.ai.disabled import DisabledProvider
from app.services.ai.fake import FakeProvider
from app.services.auth import AuthError
from app.services.proposals import ProposalService
from app.services.schedules import ScheduleService


def settings(**changes):
    return Settings(
        _env_file=None, proposal_signing_key="fictional-signing-key-32-characters-only", **changes
    )


def test_disabled_is_default_and_fake_cannot_be_selected_from_configuration():
    assert isinstance(get_provider(settings()), DisabledProvider)
    assert isinstance(get_provider(settings(ai_enabled=True, ai_provider="fake")), DisabledProvider)
    with pytest.raises(AuthError) as error:
        get_provider(settings()).generate({}, {})
    assert error.value.status == 503


def test_external_provider_requires_explicit_configuration_and_secrets_are_redacted():
    value = settings(ai_enabled=True, ai_provider="gemini", ai_api_key="fictional-secret")
    assert isinstance(get_provider(value), DisabledProvider)
    value.ai_allow_external_data = True
    assert get_provider(value).external
    assert "fictional-secret" not in repr(value)
    assert "fictional-signing-key" not in repr(value)


def test_receipt_is_bound_to_session_schedule_signature_and_expiry(monkeypatch):
    identifier = uuid4()
    service = ProposalService(None, settings(), "s" * 43, FakeProvider())
    operation = {"action": "remove", "day_id": str(uuid4()), "assignment_id": str(uuid4())}
    monkeypatch.setattr("app.services.proposals.time.time", lambda: 1000)
    receipt = service.sign(
        {
            "schedule": str(identifier),
            "session": service.session_hash,
            "version": 1,
            "expires": 1600,
            "operations": [operation],
        }
    )
    assert service.verify(receipt, identifier)[0]["version"] == 1
    for alternate in (receipt + "x", receipt.replace(".", "x.", 1)):
        with pytest.raises(AuthError):
            service.verify(alternate, identifier)
    with pytest.raises(AuthError):
        service.verify(receipt, uuid4())
    with pytest.raises(AuthError):
        ProposalService(None, settings(), "t" * 43, FakeProvider()).verify(receipt, identifier)
    monkeypatch.setattr("app.services.proposals.time.time", lambda: 1600)
    with pytest.raises(AuthError):
        service.verify(receipt, identifier)


def test_proposal_confirmation_is_strict_and_operations_forbid_arbitrary_commands():
    for value in (False, 1, "true"):
        with pytest.raises(ValidationError):
            ProposalConfirm(receipt="fictional-receipt", confirmed=value)
    with pytest.raises(ValidationError):
        Operation(action="publish", day_id="D1")
    with pytest.raises(ValidationError):
        Operation(action="remove", day_id="D1", sql="DROP TABLE")


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/assistant/status"),
        ("post", "/assistant/communications"),
        ("post", f"/schedules/{uuid4()}/proposals/preview"),
        ("post", f"/schedules/{uuid4()}/proposals/confirm"),
    ],
)
def test_assistant_endpoints_require_authenticated_session(client, method, path):
    response = getattr(client, method)("/api/v1" + path)
    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"


def test_status_is_safe_and_communications_need_csrf_and_consent(monkeypatch):
    from app.api.v1 import assistant

    app = create_app(settings())
    app.dependency_overrides[require_auth] = lambda: {"user": {"id": "fictional"}}
    headers = {"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"}
    with TestClient(app) as client:
        status = client.get("/api/v1/assistant/status")
        assert status.status_code == 200
        assert status.json() == {
            "enabled": False,
            "provider": "disabled",
            "external_data": False,
            "proposals_enabled": False,
        }
        body = {"text": "Mensagem ficticia", "intent": "draft"}
        assert client.post("/api/v1/assistant/communications", json=body).status_code == 403
        assert (
            client.post("/api/v1/assistant/communications", json=body, headers=headers).status_code
            == 503
        )
        provider = FakeProvider({"subject": "Assunto ficticio", "body": "Texto revisado"})
        provider.external = True
        monkeypatch.setattr(assistant, "get_provider", lambda _: provider)
        assert (
            client.post("/api/v1/assistant/communications", json=body, headers=headers).status_code
            == 403
        )
        assert not provider.calls
        response = client.post(
            "/api/v1/assistant/communications",
            json={**body, "consent_external": True},
            headers=headers,
        )
        assert response.json() == {"subject": "Assunto ficticio", "body": "Texto revisado"}
        assert len(provider.calls) == 1


@pytest.fixture
def prepared(db_session):
    unit = Unit(name="Unidade teste privada")
    db_session.add(unit)
    db_session.flush()
    employee = Employee(display_name="Pessoa teste privada", home_unit_id=unit.id)
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
    detail = ScheduleService(db_session).create(ScheduleCreate(week_start=date(2026, 11, 23)))
    provider = FakeProvider(
        {
            "status": "ready",
            "message": "Ajustar periodo explicitamente",
            "operations": [
                {
                    "action": "patch",
                    "day_id": "D1",
                    "assignment_id": "A1",
                    "unit_id": "U1",
                    "times": {
                        "start_time": "09:00",
                        "end_time": "16:00",
                        "break_start_time": None,
                        "break_end_time": None,
                        "position": None,
                    },
                }
            ],
        }
    )
    service = ProposalService(db_session, settings(), "s" * 43, provider)
    return service, detail, employee, unit


def preview(service, detail):
    return service.preview(
        detail["id"],
        ProposalPreview(
            expected_version=detail["version"],
            request="Ajuste E1 em 2026-11-23 para 09:00-16:00 na U1",
            reference_date=date(2026, 11, 23),
        ),
    )


@pytest.mark.integration
def test_preview_does_not_write_and_confirm_changes_only_draft_once(prepared):
    service, detail, employee, unit = prepared
    employee_name, employee_id = employee.display_name, str(employee.id)
    unit_name, unit_id = unit.name, str(unit.id)
    generate = service.provider.generate

    def without_database_transaction(prompt, schema):
        assert not service.db.in_transaction()
        return generate(prompt, schema)

    service.provider.generate = without_database_transaction
    result = preview(service, detail)
    assert result["status"] == "ready"
    assert service.schedules.detail(detail["id"])["version"] == 1
    assert service.db.scalar(select(ScheduleAssignment.start_time)) == time(8)
    prompt = str(service.provider.calls[0])
    for secret in (employee_name, unit_name, employee_id, unit_id):
        assert secret not in prompt
    confirmed = service.confirm(
        detail["id"], ProposalConfirm(receipt=result["receipt"], confirmed=True)
    )
    assert confirmed["version"] == 2
    assert confirmed["status"] == "draft"
    assert service.db.scalar(select(ScheduleAssignment.start_time)) == time(9)
    assert service.db.scalar(
        select(EmployeeWorkPattern.start_time).where(EmployeeWorkPattern.weekday == 0)
    ) == time(8)
    assert service.db.scalar(select(func.count()).select_from(ScheduleRevision)) == 0
    with pytest.raises(AuthError) as error:
        service.confirm(detail["id"], ProposalConfirm(receipt=result["receipt"], confirmed=True))
    assert error.value.status == 409


@pytest.mark.integration
def test_confirmation_rechecks_new_absence_and_rolls_back(prepared):
    service, detail, employee, _ = prepared
    result = preview(service, detail)
    service.db.add(
        Absence(
            employee_id=employee.id,
            type="day_off",
            mode="full_day",
            start_date=date(2026, 11, 23),
            end_date=date(2026, 11, 23),
        )
    )
    service.db.commit()
    with pytest.raises(AuthError) as error:
        service.confirm(detail["id"], ProposalConfirm(receipt=result["receipt"], confirmed=True))
    assert error.value.status == 409
    assert service.db.scalar(select(ScheduleAssignment.start_time)) == time(8)
    assert service.schedules.detail(detail["id"])["version"] == 1


@pytest.mark.integration
def test_mixed_valid_invalid_proposal_has_no_partial_writes(prepared):
    service, detail, _, _ = prepared
    operation = service.provider.result["operations"][0]
    service.provider.result["operations"] = [operation, {**operation, "assignment_id": "A999"}]
    result = preview(service, detail)
    assert result["status"] == "needs_clarification"
    assert result["receipt"] is None
    assert service.db.scalar(select(ScheduleAssignment.start_time)) == time(8)


@pytest.mark.integration
def test_unknown_duration_and_inactive_unit_block_proposals(prepared):
    service, detail, _, unit = prepared
    unit.active = False
    service.db.commit()
    assert preview(service, detail)["status"] != "ready"


@pytest.mark.integration
def test_failed_commit_rolls_back_all_assignment_changes(prepared, monkeypatch):
    service, detail, _, _ = prepared
    result = preview(service, detail)

    def fail_commit():
        service.db.flush()
        raise OperationalError("fictional failure", {}, Exception("fictional"))

    with monkeypatch.context() as patch:
        patch.setattr(service.db, "commit", fail_commit)
        with pytest.raises(OperationalError):
            service.confirm(
                detail["id"], ProposalConfirm(receipt=result["receipt"], confirmed=True)
            )
    assert service.db.scalar(select(ScheduleAssignment.start_time)) == time(8)
    assert service.schedules.detail(detail["id"])["version"] == 1


@pytest.mark.integration
def test_external_preview_requires_consent_before_call(prepared):
    service, detail, _, _ = prepared
    service.provider.external = True
    with pytest.raises(AuthError) as error:
        preview(service, detail)
    assert error.value.status == 403
    assert not service.provider.calls


@pytest.mark.integration
def test_frozen_unknown_duration_requires_manual_resolution(prepared):
    from app.models.schedule import ScheduleEmployeeDay

    service, detail, _, _ = prepared
    day = service.db.get(ScheduleEmployeeDay, detail["days"][0]["id"])
    day.source_data = {"weekday": 0, "state": "pending", "start_time": None, "end_time": None}
    service.db.commit()
    result = preview(service, detail)
    assert result["status"] == "blocked"
    assert result["receipt"] is None


@pytest.mark.integration
def test_known_homonyms_request_requires_clarification_without_model_call(prepared):
    service, detail, employee, _ = prepared
    service.db.add(Employee(display_name=employee.display_name))
    service.db.commit()
    other = service.schedules.create(ScheduleCreate(week_start=date(2026, 11, 30)))
    result = service.preview(
        other["id"],
        ProposalPreview(
            expected_version=1,
            request="Ajuste Pessoa teste privada",
            reference_date=date(2026, 11, 30),
        ),
    )
    assert result["status"] == "needs_clarification"
    assert not service.provider.calls


@pytest.mark.integration
def test_ambiguous_model_response_never_receives_receipt(prepared):
    service, detail, _, _ = prepared
    service.provider.result = {
        "status": "needs_clarification",
        "message": "Qual periodo?",
        "operations": [],
    }
    result = preview(service, detail)
    assert result["status"] == "needs_clarification"
    assert result["receipt"] is None


@pytest.mark.parametrize("missing", ["position", "break_start_time", "break_end_time"])
def test_patch_requires_explicit_nullable_fields(missing):
    times = {
        "start_time": "09:00",
        "end_time": "16:00",
        "break_start_time": None,
        "break_end_time": None,
        "position": "Posto ficticio",
    }
    complete = Operation(action="patch", day_id="D1", assignment_id="A1", unit_id="U1", times=times)
    assert complete.times.position == "Posto ficticio"
    del times[missing]
    with pytest.raises(ValidationError):
        Operation(action="patch", day_id="D1", assignment_id="A1", unit_id="U1", times=times)


@pytest.mark.integration
def test_incomplete_patch_needs_clarification_and_complete_patch_preserves_context(prepared):
    service, detail, _, _ = prepared
    row = service.db.scalar(select(ScheduleAssignment))
    row.position = "Posto preservado ficticio"
    row.break_start_time, row.break_end_time = time(12), time(13)
    service.db.commit()
    values = service.provider.result["operations"][0]["times"]
    del values["position"]
    result = preview(service, detail)
    assert result["status"] == "needs_clarification"
    assert result["receipt"] is None
    context = service.provider.calls[-1]["days"][0]["assignments"][0]
    assert context["position"] == "Posto preservado ficticio"
    assert context["break_start_time"] == "12:00:00"
    values.update(
        position=context["position"],
        break_start_time=context["break_start_time"],
        break_end_time=context["break_end_time"],
    )
    result = preview(service, detail)
    assert result["status"] == "ready"
    service.confirm(detail["id"], ProposalConfirm(receipt=result["receipt"], confirmed=True))
    row = service.db.scalar(select(ScheduleAssignment))
    assert row.position == "Posto preservado ficticio"
    assert (row.break_start_time, row.break_end_time) == (time(12), time(13))


@pytest.mark.integration
def test_names_with_common_prefix_are_resolved_longest_first(prepared):
    service, _, employee, unit = prepared
    employee.display_name = "Ana Maria"
    unit.name = "Central Norte"
    service.db.add(Employee(display_name="Ana"))
    service.db.add(Unit(name="Central"))
    service.db.commit()
    detail = service.schedules.create(ScheduleCreate(week_start=date(2026, 11, 30)))
    service.provider.result = {
        "status": "needs_clarification",
        "message": "Informe horario",
        "operations": [],
    }
    service.preview(
        detail["id"],
        ProposalPreview(
            expected_version=1,
            request="Ajuste Ana Maria na Central Norte em 2026-11-30",
            reference_date=date(2026, 11, 30),
        ),
    )
    request = service.provider.calls[-1]["request"]
    assert "Maria" not in request and "Norte" not in request
    assert "Ana" not in request and "Central" not in request
    employee_alias = next(
        day["employee"] for day in service.provider.calls[-1]["days"] if day["day_id"] == "D2"
    )
    assert employee_alias in request


@pytest.mark.integration
def test_cross_category_prefix_replacement_is_a_single_pass(prepared):
    service, _, employee, unit = prepared
    employee.display_name = "Ana"
    unit.name = "Ana Nery"
    service.db.commit()
    detail = service.schedules.create(ScheduleCreate(week_start=date(2026, 11, 30)))
    service.provider.result = {
        "status": "needs_clarification",
        "message": "Informe horario",
        "operations": [],
    }
    service.preview(
        detail["id"],
        ProposalPreview(
            expected_version=1,
            request="Ajuste Ana na Ana Nery em 2026-11-30",
            reference_date=date(2026, 11, 30),
        ),
    )
    request = service.provider.calls[-1]["request"]
    assert request == "Ajuste E1 na U1 em 2026-11-30"


@pytest.mark.integration
def test_employee_uuid_can_disambiguate_a_request_without_being_sent(prepared):
    service, detail, employee, _ = prepared
    employee_id = str(employee.id)
    service.provider.result = {
        "status": "needs_clarification",
        "message": "Informe horario",
        "operations": [],
    }
    service.preview(
        detail["id"],
        ProposalPreview(
            expected_version=1,
            request=f"Ajuste {employee_id} em 2026-11-23",
            reference_date=date(2026, 11, 23),
        ),
    )
    request = service.provider.calls[-1]["request"]
    assert request == "Ajuste E1 em 2026-11-23"
    assert employee_id not in str(service.provider.calls[-1])
