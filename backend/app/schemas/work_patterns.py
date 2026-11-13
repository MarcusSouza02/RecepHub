from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TIME_FIELDS = ("start_time", "end_time", "break_start_time", "break_end_time")


class WorkPatternDay(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weekday: int = Field(ge=0, le=6, strict=True)
    state: Literal["pending", "working", "non_working"]
    start_time: time | None = None
    end_time: time | None = None
    break_start_time: time | None = None
    break_end_time: time | None = None

    @field_validator(*TIME_FIELDS, mode="before")
    @classmethod
    def time_input(cls, value):
        if value is not None and not isinstance(value, (str, time)):
            raise ValueError("Informe um horário local")
        return value

    @field_validator(*TIME_FIELDS)
    @classmethod
    def minute_precision(cls, value):
        if value is not None and (value.second or value.microsecond or value.tzinfo is not None):
            raise ValueError("Horário exige precisão de minutos e nenhum fuso")
        return value

    @model_validator(mode="after")
    def intervals(self):
        if self.state != "working" and any(getattr(self, name) is not None for name in TIME_FIELDS):
            raise ValueError("Dias pendentes ou sem jornada não aceitam horários")
        start, end, pause, resume = (getattr(self, name) for name in TIME_FIELDS)
        if start is not None and end is not None and start >= end:
            raise ValueError("A saída deve ser posterior à entrada no mesmo dia")
        if pause is not None and resume is not None and pause >= resume:
            raise ValueError("O fim do intervalo deve ser posterior ao início")
        for boundary in (pause, resume):
            if boundary is not None and (
                (start is not None and boundary < start) or (end is not None and boundary > end)
            ):
                raise ValueError("O intervalo deve estar contido na jornada")
        return self

    @property
    def is_complete(self):
        return self.state == "non_working" or (
            self.state == "working"
            and self.start_time is not None
            and self.end_time is not None
            and ((self.break_start_time is None) == (self.break_end_time is None))
        )

    @property
    def duration_minutes(self):
        if not self.is_complete:
            return None
        if self.state == "non_working":
            return 0

        def minutes(value):
            return value.hour * 60 + value.minute

        result = minutes(self.end_time) - minutes(self.start_time)
        if self.break_start_time is not None:
            result -= minutes(self.break_end_time) - minutes(self.break_start_time)
        return result


class WorkPatternPut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days: list[WorkPatternDay] = Field(min_length=7, max_length=7)

    @model_validator(mode="after")
    def seven_unique_days(self):
        if {day.weekday for day in self.days} != set(range(7)):
            raise ValueError("Informe os sete dias sem repetição")
        return self
