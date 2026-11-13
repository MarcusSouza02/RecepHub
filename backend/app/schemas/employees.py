from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EmployeeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=140)
    home_unit_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=500)
    active: bool = Field(default=True, strict=True)

    @field_validator("display_name", mode="before")
    @classmethod
    def trim_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class EmployeePatch(EmployeeCreate):
    display_name: str | None = Field(default=None, min_length=1, max_length=140)
    active: bool | None = Field(default=None, strict=True)

    @model_validator(mode="after")
    def valid_patch(self):
        if not self.model_fields_set:
            raise ValueError("Informe pelo menos um campo")
        for field in ("display_name", "active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} não pode ser nulo")
        return self


class EmployeeQuery(BaseModel):
    q: str | None = Field(default=None, max_length=140)
    status: Literal["active", "inactive", "all"] = "active"
    home_unit_id: UUID | None = None
    without_home_unit: bool = False
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def exclusive_unit(self):
        if self.home_unit_id is not None and self.without_home_unit:
            raise ValueError("Filtros de unidade são mutuamente exclusivos")
        return self


class EmployeePublic(BaseModel):
    id: UUID
    display_name: str
    home_unit_id: UUID | None
    home_unit_name: str | None
    home_unit_active: bool | None
    notes: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class EmployeePage(BaseModel):
    items: list[EmployeePublic]
    total: int
    page: int
    page_size: int
