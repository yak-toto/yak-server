from typing import Generic, TypeVar

from pydantic import ConstrainedInt, Extra
from pydantic.generics import GenericModel

Result = TypeVar("Result")


class GenericOut(GenericModel, Generic[Result], extra=Extra.forbid):
    ok: bool = True
    result: Result


class PositiveOrZeroInt(ConstrainedInt):
    gt = -1
