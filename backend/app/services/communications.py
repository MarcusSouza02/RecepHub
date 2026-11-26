from datetime import date, timedelta

from fastapi.encoders import jsonable_encoder

from app.schemas.communications import DraftSource
from app.services.schedules import ScheduleService

LABELS = {
    "publication": "Publicação de escala",
    "schedule_update": "Atualização de escala",
    "time_change": "Alteração de horário",
    "unit_change": "Mudança de unidade",
    "coverage": "Cobertura",
    "notice": "Aviso geral",
}


class CommunicationService:
    def __init__(self, db):
        self.db = db

    def prepare(self, payload):
        context = None
        reference = ""
        try:
            if payload.source is not None:
                service = ScheduleService(self.db)
                if isinstance(payload.source, DraftSource):
                    service.get(payload.schedule_id, payload.source.expected_version)
                    context = jsonable_encoder(service.detail(payload.schedule_id))
                    reference = (
                        f"RASCUNHO · versão {payload.source.expected_version} · não publicado"
                    )
                else:
                    revision = service.revision(payload.schedule_id, payload.source.revision_number)
                    context = jsonable_encoder(revision["snapshot"])
                    reference = f"Publicado · revisão {revision['number']}"
            # Release snapshot read locks before preparing any presentation content.
            self.db.rollback()
        except Exception:
            self.db.rollback()
            raise
        title = LABELS[payload.type]
        body = [title]
        suffix = ""
        if context is not None:
            start = date.fromisoformat(str(context["week_start"]))
            end = start + timedelta(days=6)
            suffix = f" · {start:%d/%m/%Y} a {end:%d/%m/%Y}"
            body += [f"Período: {start:%d/%m/%Y} a {end:%d/%m/%Y}", reference]
            units = sorted(
                {
                    assignment["unit_name"]
                    for day in context.get("days", [])
                    for assignment in day.get("assignments", [])
                }
            )
            body.append("Unidades: " + (", ".join(units) if units else "sem alocações"))
        if payload.message:
            body += ["", payload.message]
        return {"subject": payload.subject or title + suffix, "body": "\n".join(body)}
