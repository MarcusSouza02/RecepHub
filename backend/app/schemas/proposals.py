from datetime import date
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.schemas.schedules import AssignmentTimes, Input, VersionInput


class ProposalPreview(VersionInput):
    request: str = Field(min_length=1, max_length=1000)
    reference_date: date
    consent_external: bool = Field(default=False, strict=True)


class ProposalConfirm(Input):
    receipt: str = Field(min_length=10, max_length=3800, repr=False)
    confirmed: bool = Field(strict=True)

    @field_validator("confirmed")
    @classmethod
    def explicit(cls, value):
        if not value:
            raise ValueError("Confirme explicitamente")
        return value


class Operation(Input):
    action: Literal["add", "patch", "remove"]
    day_id: str = Field(max_length=40)
    assignment_id: str | None = Field(default=None, max_length=40)
    unit_id: str | None = Field(default=None, max_length=40)
    times: AssignmentTimes | None = None

    @model_validator(mode="after")
    def explicit_patch_fields(self):
        if self.action == "patch" and (
            self.times is None
            or self.unit_id is None
            or not {
                "start_time",
                "end_time",
                "break_start_time",
                "break_end_time",
                "position",
            }.issubset(self.times.model_fields_set)
        ):
            raise ValueError("Patch exige todos os campos, inclusive intervalos e posto nulos")
        return self


class ModelProposal(Input):
    status: Literal["ready", "needs_clarification", "blocked"]
    message: str = Field(max_length=500)
    operations: list[Operation] = Field(default_factory=list, max_length=5)


class CommunicationInput(Input):
    text: str = Field(min_length=1, max_length=2000)
    intent: Literal["draft", "revise"]
    consent_external: bool = Field(default=False, strict=True)


class CommunicationOutput(Input):
    subject: str = Field(max_length=180)
    body: str = Field(max_length=3000)
