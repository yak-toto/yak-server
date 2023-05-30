from typing import TYPE_CHECKING, List

from pydantic import UUID4, BaseModel

from .phases import PhaseOut

if TYPE_CHECKING:
    from yak_server.database.models import GroupModel


class GroupIn(BaseModel):
    id: UUID4


class GroupOut(BaseModel):
    id: UUID4
    code: str
    description: str

    @classmethod
    def from_instance(cls, group: "GroupModel") -> "GroupOut":
        return cls(id=group.id, code=group.code, description=group.description_fr)


class Phase(BaseModel):
    id: UUID4


class GroupWithPhaseIdOut(BaseModel):
    id: UUID4
    code: str
    phase: Phase
    description: str

    @classmethod
    def from_instance(cls, group: "GroupModel") -> "GroupWithPhaseIdOut":
        return cls(
            id=group.id,
            code=group.code,
            phase=Phase(id=group.phase_id),
            description=group.description_fr,
        )


class AllGroupsResponse(BaseModel):
    phases: List[PhaseOut]
    groups: List[GroupWithPhaseIdOut]


class GroupResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut


class GroupsByPhaseCodeResponse(BaseModel):
    phase: PhaseOut
    groups: List[GroupOut]
