from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RevisionSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["revision"]
    revision_number: int = Field(ge=1, strict=True)


class DraftSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["draft"]
    expected_version: int = Field(ge=1, strict=True)


class ExportInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Annotated[RevisionSource | DraftSource, Field(discriminator="kind")]
    unit_id: UUID | None = None
    work_date: date | None = None
    format: Literal["pdf", "png"] = "pdf"
    page: int = Field(default=1, ge=1, le=30, strict=True)
