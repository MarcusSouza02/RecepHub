from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.auth import require_auth
from app.api.v1.communications import router
from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from app.schemas.communications import CommunicationPrepare
from app.services.auth import AuthError
from app.services.communications import CommunicationService


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "notice", "subject": "Aviso\r\nBcc: teste@example.invalid"},
        {"type": "notice", "schedule_id": str(uuid4())},
        {"type": "publication"},
        {"type": "notice", "message": "x" * 2001},
        {"type": "notice", "recipient": "teste@example.invalid"},
        {"type": "notice", "source": {"kind": "revision", "revision_number": 0}},
    ],
)
def test_invalid_communication_input(payload):
    with pytest.raises(ValidationError):
        CommunicationPrepare.model_validate(payload)


def test_manual_notice_preserves_accents_and_does_not_write():
    db = Mock()
    result = CommunicationService(db).prepare(
        CommunicationPrepare(type="notice", message="Atenção: São João")
    )
    assert result == {"subject": "Aviso geral", "body": "Aviso geral\n\nAtenção: São João"}
    db.commit.assert_not_called()
    db.add.assert_not_called()
    db.rollback.assert_called_once()


def test_revision_uses_immutable_server_snapshot_and_releases_lock():
    db = Mock()
    snapshot = {"week_start": "2026-11-23", "days": [{"assignments": [{"unit_name": "São João"}]}]}
    with patch("app.services.communications.ScheduleService") as service:
        service.return_value.revision.return_value = {"number": 2, "snapshot": snapshot}
        result = CommunicationService(db).prepare(
            CommunicationPrepare.model_validate(
                {
                    "type": "publication",
                    "schedule_id": str(uuid4()),
                    "source": {"kind": "revision", "revision_number": 2},
                }
            )
        )
        service.return_value.detail.assert_not_called()
    assert "23/11/2026 a 29/11/2026" in result["subject"]
    assert "Publicado · revisão 2" in result["body"]
    assert "Unidades: São João" in result["body"]
    db.rollback.assert_called_once()


def test_obsolete_draft_does_not_prepare_text():
    db = Mock()
    with patch("app.services.communications.ScheduleService") as service:
        service.return_value.get.side_effect = AuthError(409, "Versão obsoleta")
        with pytest.raises(AuthError):
            CommunicationService(db).prepare(
                CommunicationPrepare.model_validate(
                    {
                        "type": "schedule_update",
                        "schedule_id": str(uuid4()),
                        "source": {"kind": "draft", "expected_version": 1},
                    }
                )
            )
    db.rollback.assert_called_once()


def test_current_draft_is_explicitly_marked_unpublished():
    db = Mock()
    schedule_id = uuid4()
    with patch("app.services.communications.ScheduleService") as service:
        service.return_value.detail.return_value = {"week_start": "2026-11-23", "days": []}
        result = CommunicationService(db).prepare(
            CommunicationPrepare.model_validate(
                {
                    "type": "time_change",
                    "schedule_id": str(schedule_id),
                    "source": {"kind": "draft", "expected_version": 3},
                }
            )
        )
        service.return_value.get.assert_called_once_with(schedule_id, 3)
    assert "RASCUNHO · versão 3 · não publicado" in result["body"]
    assert "Unidades: sem alocações" in result["body"]
    db.commit.assert_not_called()


def test_endpoint_requires_authentication_and_csrf():
    app = create_app(Settings(_env_file=None))
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_session] = lambda: Mock()
    with TestClient(app) as client:
        assert (
            client.post("/api/v1/communications/prepare", json={"type": "notice"}).status_code
            == 401
        )
        app.dependency_overrides[require_auth] = lambda: {"username": "fictional"}
        assert (
            client.post("/api/v1/communications/prepare", json={"type": "notice"}).status_code
            == 403
        )
        response = client.post(
            "/api/v1/communications/prepare",
            json={"type": "notice", "message": "Aviso fictício"},
            headers={"Origin": "http://localhost:3000", "X-RecepHub-CSRF": "1"},
        )
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["body"].endswith("Aviso fictício")
