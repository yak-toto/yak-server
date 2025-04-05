from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

Result = TypeVar("Result")


class GenericOut(BaseModel, Generic[Result]):
    ok: bool = True
    result: Result

    model_config = ConfigDict(extra="forbid")


class ErrorOut(BaseModel):
    ok: bool = False
    error_code: int
    description: str

    model_config = ConfigDict(extra="forbid")


class SingleValidationErrorOut(BaseModel):
    field: str
    error: str


class ValidationErrorOut(BaseModel):
    ok: bool = False
    error_code: int

    description: list[SingleValidationErrorOut]

    model_config = ConfigDict(extra="forbid")
