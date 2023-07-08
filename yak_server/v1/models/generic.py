from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

Result = TypeVar("Result")


class GenericOut(BaseModel, Generic[Result]):
    ok: bool = True
    result: Result

    model_config = ConfigDict(extra="forbid")
