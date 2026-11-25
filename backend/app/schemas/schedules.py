from datetime import date, time, timedelta
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.work_patterns import WorkPatternDay


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScheduleCreate(Input):
    week_start: date

    @field_validator("week_start")
    @classmethod
    def monday(cls, value):
        if value.weekday() != 0 or value > date.max - timedelta(days=6):
            raise ValueError("A semana deve começar na segunda-feira")
        return value


class ScheduleQuery(Input):
    from_date: date | None = None
    to_date: date | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("Período inválido")
        return self


class VersionInput(Input):
    expected_version: int = Field(ge=1, strict=True)


class AssignmentTimes(Input):
    start_time: time
    end_time: time
    break_start_time: time | None = None
    break_end_time: time | None = None
    position: str | None = Field(default=None, max_length=80)

    @field_validator("start_time", "end_time", "break_start_time", "break_end_time", mode="before")
    @classmethod
    def local_time_input(cls, value):
        if value is not None and not isinstance(value, (str, time)):
            raise ValueError("Informe um horário local")
        return value

    @model_validator(mode="after")
    def valid_times(self):
        day = WorkPatternDay(
            weekday=0,
            state="working",
            **{
                key: getattr(self, key)
                for key in ("start_time", "end_time", "break_start_time", "break_end_time")
            },
        )
        if not day.is_complete:
            raise ValueError("Informe o intervalo completo")
        return self


class AssignmentCreate(AssignmentTimes, VersionInput):
    day_id: UUID
    unit_id: UUID


class AssignmentPatch(VersionInput):
    unit_id: UUID | None = None
    start_time: time | None = None
    end_time: time | None = None
    break_start_time: time | None = None
    break_end_time: time | None = None
    position: str | None = Field(default=None, max_length=80)

    @field_validator("start_time", "end_time", "break_start_time", "break_end_time", mode="before")
    @classmethod
    def local_time_input(cls, value):
        return AssignmentTimes.local_time_input(value)

    @model_validator(mode="after")
    def changes(self):
        if not self.model_fields_set - {"expected_version"}:
            raise ValueError("Informe uma alteração")
        for key in ("unit_id", "start_time", "end_time"):
            if key in self.model_fields_set and getattr(self, key) is None:
                raise ValueError("Campo obrigatório não pode ser nulo")
        return self


class DayPatch(VersionInput):
    state: Literal["pending", "working", "non_working", "excluded"]
    resolution_note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def exclusion_reason(self):
        if self.state == "excluded" and not (self.resolution_note or "").strip():
            raise ValueError("Informe o motivo da exclusão")
        return self


class PublishInput(VersionInput):
    confirmed: bool = Field(strict=True)

    @field_validator("confirmed")
    @classmethod
    def explicit_confirmation(cls, value):
        if value is not True:
            raise ValueError("Confirme explicitamente a publicação")
        return value
