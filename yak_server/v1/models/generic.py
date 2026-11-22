from typing import Generic, TypeVar

from pydantic import BaseModel

from yak_server.helpers.errors import ErrorCode

Result = TypeVar("Result")


class GenericOut(BaseModel, Generic[Result]):
    ok: bool = True
    result: Result


class ErrorOut(BaseModel):
    ok: bool = False
    error_code: ErrorCode
    description: str


class SingleValidationErrorOut(BaseModel):
    field: str
    error: str


class ValidationErrorOut(BaseModel):
    ok: bool = False
    error_code: ErrorCode

    description: list[SingleValidationErrorOut]
