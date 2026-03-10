from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from yak_server.helpers.errors import ErrorCode

Result = TypeVar("Result")


class GenericOut(BaseModel, Generic[Result]):
    ok: bool = True
    result: Result

    model_config = ConfigDict(extra="forbid")


class ErrorOut(BaseModel):
    ok: bool = False
    error_code: ErrorCode
    description: str

    model_config = ConfigDict(extra="forbid")


class SingleValidationErrorOut(BaseModel):
    field: str
    error: str


class ValidationErrorOut(BaseModel):
    ok: bool = False
    error_code: ErrorCode

    description: list[SingleValidationErrorOut]

    model_config = ConfigDict(extra="forbid")
