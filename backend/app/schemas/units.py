from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class UnitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=1, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    active: bool = True

    @field_validator("name", "city", "description", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("city", "description")
    @classmethod
    def empty_to_none(cls, value):
        return value or None


class UnitPatch(UnitCreate):
    name: str = Field(default=None, min_length=1, max_length=120)
    active: bool = Field(default=None)

    @model_validator(mode="after")
    def nonempty_patch(self):
        if not self.model_fields_set:
            raise ValueError("Informe campos para atualizar")
        return self


class UnitQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    q: str = Field(default="", max_length=120)
    status: Literal["active", "inactive", "all"] = "active"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class UnitOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    city: str | None
    description: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
