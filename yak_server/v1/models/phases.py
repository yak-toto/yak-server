from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel

if TYPE_CHECKING:
    from yak_server.database.models import PhaseModel


class PhaseOut(BaseModel):
    id: UUID4
    code: str
    description: str

    @classmethod
    def from_instance(cls, phase: "PhaseModel") -> "PhaseOut":
        return cls(
            id=phase.id,
            code=phase.code,
            description=phase.description_fr,
        )
