from datetime import date, time
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.schedules import VersionInput


class CoveragePreview(VersionInput):
    work_date: date
    unit_id: UUID
    start_time: time
    end_time: time
    position: str | None = Field(default=None, max_length=80)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def local_input(cls, value):
        if not isinstance(value, (str, time)):
            raise ValueError("Informe um horário local")
        return value

    @model_validator(mode="after")
    def valid_period(self):
        for value in (self.start_time, self.end_time):
            if value.tzinfo or value.second or value.microsecond:
                raise ValueError("Informe horários locais com precisão de minuto")
        if self.start_time >= self.end_time:
            raise ValueError("Período inválido")
        return self


class CoverageConfirm(CoveragePreview):
    employee_id: UUID
    confirmed: bool = Field(strict=True)

    @field_validator("confirmed")
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError("Confirme a cobertura")
        return value
