from datetime import date, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AbsenceType = Literal["vacation", "day_off", "compensation", "other"]
AbsenceMode = Literal["full_day", "partial"]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AbsenceFields(Input):
    type: AbsenceType
    mode: AbsenceMode
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def local_time_input(cls, value):
        if value is not None and not isinstance(value, (str, time)):
            raise ValueError("Informe um horário local")
        return value

    @field_validator("start_time", "end_time")
    @classmethod
    def minute_precision(cls, value):
        if value is not None and (value.tzinfo or value.second or value.microsecond):
            raise ValueError("Informe horário local com precisão de minuto")
        return value

    @model_validator(mode="after")
    def valid_period(self):
        if self.start_date > self.end_date:
            raise ValueError("Datas fora de ordem")
        if self.mode == "full_day":
            if self.start_time is not None or self.end_time is not None:
                raise ValueError("Dia inteiro não admite horários")
        elif (
            self.start_date != self.end_date
            or self.start_time is None
            or self.end_time is None
            or self.start_time >= self.end_time
        ):
            raise ValueError("Período parcial inválido")
        return self


class AbsenceCreate(AbsenceFields):
    employee_id: UUID


class AbsencePatch(Input):
    expected_version: int = Field(strict=True, ge=1)
    type: AbsenceType | None = None
    mode: AbsenceMode | None = None
    start_date: date | None = None
    end_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    notes: str | None = Field(default=None, max_length=500)

    _local = field_validator("start_time", "end_time", mode="before")(
        AbsenceFields.local_time_input.__func__
    )
    _minute = field_validator("start_time", "end_time")(AbsenceFields.minute_precision.__func__)

    @model_validator(mode="after")
    def nonempty(self):
        if not self.model_fields_set - {"expected_version"}:
            raise ValueError("Informe uma alteração")
        for key in ("type", "mode", "start_date", "end_date"):
            if key in self.model_fields_set and getattr(self, key) is None:
                raise ValueError("Campo obrigatório")
        return self


class AbsenceCancel(Input):
    expected_version: int = Field(strict=True, ge=1)
    confirmed: bool = Field(strict=True)

    @field_validator("confirmed")
    @classmethod
    def confirmation(cls, value):
        if value is not True:
            raise ValueError("Confirme o cancelamento")
        return value


class AbsenceQuery(Input):
    employee_id: UUID | None = None
    type: AbsenceType | None = None
    status: Literal["active", "cancelled", "all"] = "active"
    from_date: date | None = None
    to_date: date | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def ordered(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("Período inválido")
        return self
