from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RevisionSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["revision"]
    revision_number: int = Field(gt=0, strict=True)


class DraftSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["draft"]
    expected_version: int = Field(gt=0, strict=True)


class CommunicationPrepare(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal[
        "publication", "schedule_update", "time_change", "unit_change", "coverage", "notice"
    ]
    schedule_id: UUID | None = None
    source: Annotated[RevisionSource | DraftSource, Field(discriminator="kind")] | None = None
    message: str | None = Field(default=None, max_length=2000)
    subject: str | None = Field(default=None, max_length=160)

    @field_validator("subject")
    @classmethod
    def safe_subject(cls, value):
        if value is not None and any(character in value for character in ("\r", "\n", "\x00")):
            raise ValueError("Assunto deve ocupar uma linha")
        return value

    @model_validator(mode="after")
    def explicit_reference(self):
        if (self.schedule_id is None) != (self.source is None):
            raise ValueError("Informe escala e origem juntas")
        if self.type == "publication" and not isinstance(self.source, RevisionSource):
            raise ValueError("Publicação exige uma revisão publicada")
        return self
