import os
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.exports import ExportInput
from app.services.auth import AuthError
from app.services.export_renderer import document_html, paginate, render_document
from app.services.exports import ExportService, export_rows


def options(**values):
    return ExportInput(source={"kind": "draft", "expected_version": 1}, **values)


def test_export_input_requires_explicit_trusted_source():
    for source in (
        {"kind": "draft"},
        {"kind": "revision"},
        {"kind": "url", "url": "https://example.com"},
        {"kind": "draft", "expected_version": True},
    ):
        with pytest.raises(ValidationError):
            ExportInput(source=source)
    with pytest.raises(ValidationError):
        options(template="<script>bad</script>")
    with pytest.raises(ValidationError):
        options(page=31)


def test_pagination_empty_and_bounds():
    assert paginate([]) == [[]]
    assert len(paginate([["a"]] * 7)) == 1
    assert len(paginate([["a"]] * 14)) == 2
    assert len(paginate([["a"]] * 100)) < 30
    for count in (391, 3001):
        with pytest.raises(AuthError) as error:
            paginate([["a"]] * count)
        assert error.value.status == 422


def test_trusted_markup_escapes_names_and_repeats_draft_warning():
    pages = paginate(
        [["2026-11-23", "<script>alert(1)</script>", "A&B", "08:00–17:00", "—", "x"]] * 14
    )
    markup = document_html(pages, "Escala <teste>", "RASCUNHO NÃO PUBLICADO · versão 3")
    assert "<script>" not in markup
    assert "&lt;script&gt;" in markup
    assert "A&amp;B" in markup
    assert markup.count("RASCUNHO NÃO PUBLICADO") == 4
    assert "Página 2 de 2" in markup
    assert "http://" not in markup


def test_export_filter_uses_frozen_names_and_no_mutation():
    unit = uuid4()
    snapshot = {
        "days": [
            {
                "work_date": "2026-11-23",
                "employee_name": "Nome congelado",
                "state": "working",
                "assignments": [
                    {
                        "unit_id": str(unit),
                        "unit_name": "Unidade congelada",
                        "start_time": "08:00:00",
                        "end_time": "17:00:00",
                        "position": None,
                    }
                ],
            }
        ]
    }
    rows = export_rows(snapshot, options(unit_id=unit))
    assert rows[0][1:4] == ["Nome congelado", "Unidade congelada", "08:00–17:00"]
    assert export_rows(snapshot, options(work_date="2026-11-24")) == []
    assert len(snapshot["days"][0]["assignments"]) == 1


def test_export_service_releases_transaction_before_renderer(monkeypatch):
    from app.services import exports

    class Database:
        released = False

        def rollback(self):
            self.released = True

    class Schedule:
        def __init__(self, db):
            self.db = db

        def get(self, schedule_id, version):
            if version != 1:
                raise AuthError(409, "obsoleta")

        def detail(self, schedule_id):
            return {"week_start": "2026-11-23", "days": []}

    db = Database()
    monkeypatch.setattr(exports, "ScheduleService", Schedule)

    def render(*args):
        assert db.released
        return b"%PDF-test"

    monkeypatch.setattr(exports, "render_document", render)
    metadata, content = ExportService(db).generate(uuid4(), options())
    assert content == b"%PDF-test"
    assert metadata["page_count"] == 1
    assert "rascunho-v1" in metadata["filename"]
    with pytest.raises(AuthError) as error:
        ExportService(db).preview(
            uuid4(), ExportInput(source={"kind": "draft", "expected_version": 2})
        )
    assert error.value.status == 409


def test_revision_export_reads_only_published_snapshot(monkeypatch):
    from app.services import exports

    class Database:
        def rollback(self):
            pass

    snapshot = {"week_start": "2026-11-23", "days": []}

    class Schedule:
        def __init__(self, db):
            pass

        def revision(self, schedule_id, number):
            assert number == 2
            return {"snapshot": snapshot}

        def detail(self, schedule_id):
            pytest.fail("Published export must not consult mutable current draft")

    monkeypatch.setattr(exports, "ScheduleService", Schedule)
    payload = ExportInput(source={"kind": "revision", "revision_number": 2})
    metadata, _, _, label = ExportService(Database()).prepare(uuid4(), payload)
    assert metadata["source"] == {"kind": "revision", "revision_number": 2}
    assert label.startswith("PUBLICADO · Revisão 2 · Escala ")
    assert snapshot == {"week_start": "2026-11-23", "days": []}


def test_export_routes_require_session(client):
    from app.api.v1.exports import router

    client.app.include_router(router, prefix="/api/v1")
    for suffix in ("/exports", "/exports/preview"):
        response = client.post(f"/api/v1/schedules/{uuid4()}{suffix}", json={})
        assert response.status_code == 401
        assert response.headers["cache-control"] == "no-store"


@pytest.mark.skipif(
    os.environ.get("RENDER_TESTS") != "1", reason="Requires installed Chromium explicitly"
)
def test_real_renderer_pdf_and_png_signature():
    markup = document_html(
        [[["2026-11-23", "Fictícia", "Unidade", "08:00–17:00", "12:00–13:00", "Recepção"]]],
        "Escala",
        "RASCUNHO NÃO PUBLICADO · versão 1",
    )
    assert render_document(markup, "pdf", 1).startswith(b"%PDF-")
    png = render_document(markup, "png", 1)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")
    assert width == 1240
    assert height == 1754


@pytest.mark.skipif(
    os.environ.get("RENDER_TESTS") != "1", reason="Requires installed Chromium explicitly"
)
def test_real_renderer_extreme_names_fit_multipage_without_cut():
    pages = paginate(
        [["2026-11-23", "W" * 140, "W" * 120, "08:00–17:00", "12:00–13:00", "W" * 80]] * 7
    )
    assert len(pages) == 4
    markup = document_html(pages, "Escala", f"RASCUNHO NÃO PUBLICADO · versão 2 · Escala {uuid4()}")
    # Renderer checks actual table/footer bounds for every page before producing either format.
    assert render_document(markup, "pdf", 1).startswith(b"%PDF-")
    assert render_document(markup, "png", 2).startswith(b"\x89PNG")
    normal_pages = paginate(
        [["2026-11-23", "Fictícia", "Unidade A", "08:00–17:00", "12:00–13:00", "Recepção"]] * 100
    )
    assert len(normal_pages) < 30
    normal_markup = document_html(normal_pages, "Escala", "PUBLICADO · Revisão 1")
    assert render_document(normal_markup, "pdf", 1).startswith(b"%PDF-")


@pytest.mark.skipif(
    os.environ.get("RENDER_TESTS") != "1", reason="Requires installed Chromium explicitly"
)
def test_real_png_later_page_has_exact_a4_raster_dimensions():
    pages = paginate(
        [["2026-11-23", "Érica fictícia", "Unidade A", "08:00–17:00", "12:00–13:00", "Recepção"]]
        * 14
    )
    assert len(pages) == 2
    markup = document_html(pages, "Escala", f"PUBLICADO · Revisão 1 · Escala {uuid4()}")
    png = render_document(markup, "png", 2)
    assert int.from_bytes(png[16:20], "big") == 1240
    assert int.from_bytes(png[20:24], "big") == 1754
