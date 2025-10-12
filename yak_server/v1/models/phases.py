from typing import TYPE_CHECKING, Union

from pydantic import UUID4, BaseModel

from yak_server.helpers.language import Lang, get_language_description

if TYPE_CHECKING:
    from yak_server_db import Phase

    from yak_server.database.models import PhaseModel


class PhaseOut(BaseModel):
    id: UUID4
    code: str
    description: str

    @classmethod
    def from_instance(cls, phase: Union["PhaseModel", "Phase"], *, lang: Lang) -> "PhaseOut":
        return cls(id=phase.id, code=phase.code, description=get_language_description(phase, lang))
