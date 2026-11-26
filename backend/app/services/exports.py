import copy

from fastapi.encoders import jsonable_encoder

from app.services.auth import AuthError
from app.services.export_renderer import LAYOUT_VERSION, document_html, paginate, render_document
from app.services.schedules import ScheduleService


def export_rows(snapshot, payload):
    rows = []
    for day in snapshot["days"]:
        if payload.work_date and day["work_date"] != payload.work_date.isoformat():
            continue
        assignments = day["assignments"]
        if payload.unit_id:
            assignments = [a for a in assignments if a["unit_id"] == str(payload.unit_id)]
            if not assignments:
                continue
        for assignment in assignments:
            pause = "—"
            if assignment.get("break_start_time") and assignment.get("break_end_time"):
                pause = f"{assignment['break_start_time'][:5]}–{assignment['break_end_time'][:5]}"
            rows.append(
                [
                    day["work_date"],
                    day["employee_name"],
                    assignment["unit_name"],
                    f"{assignment['start_time'][:5]}–{assignment['end_time'][:5]}",
                    pause,
                    assignment.get("position") or "—",
                ]
            )
        if not assignments and not payload.unit_id:
            state = {
                "pending": "Pendente",
                "non_working": "Sem trabalho",
                "excluded": "Retirada",
                "working": "Sem período",
            }.get(day["state"], "Pendente")
            rows.append([day["work_date"], day["employee_name"], "—", "—", "—", state])
    return rows


class ExportService:
    def __init__(self, db):
        self.db = db

    def prepare(self, schedule_id, payload):
        service = ScheduleService(self.db)
        try:
            if payload.source.kind == "revision":
                revision = service.revision(schedule_id, payload.source.revision_number)
                snapshot = copy.deepcopy(jsonable_encoder(revision["snapshot"]))
                label = f"PUBLICADO · Revisão {payload.source.revision_number}"
                identifier = f"revisao-{payload.source.revision_number}"
            else:
                service.get(schedule_id, payload.source.expected_version)
                snapshot = copy.deepcopy(jsonable_encoder(service.detail(schedule_id)))
                label = f"RASCUNHO NÃO PUBLICADO · versão {payload.source.expected_version}"
                identifier = f"rascunho-v{payload.source.expected_version}"
        finally:
            # Read-only transaction ends before expensive rendering; no connection/row lock held.
            self.db.rollback()
        label = f"{label} · Escala {schedule_id}"
        rows = export_rows(snapshot, payload)
        pages = paginate(rows)
        if payload.page > len(pages):
            raise AuthError(422, "Página fora do documento")
        filename = f"recephub-{snapshot['week_start']}-{identifier}"
        if payload.format == "png":
            filename += f"-pagina-{payload.page}"
        metadata = {
            "page_count": len(pages),
            "layout_version": LAYOUT_VERSION,
            "source": payload.source.model_dump(),
            "filename": f"{filename}.{payload.format}",
        }
        return metadata, pages, f"Escala semanal · {snapshot['week_start']}", label

    def preview(self, schedule_id, payload):
        return self.prepare(schedule_id, payload)[0]

    def generate(self, schedule_id, payload):
        metadata, pages, title, label = self.prepare(schedule_id, payload)
        content = render_document(document_html(pages, title, label), payload.format, payload.page)
        return metadata, content
