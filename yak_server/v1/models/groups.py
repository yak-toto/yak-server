from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel

from yak_server.helpers.language import Lang, get_language_description

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
    def from_instance(cls, group: "GroupModel", *, lang: Lang) -> "GroupOut":
        return cls(id=group.id, code=group.code, description=get_language_description(group, lang))


class Phase(BaseModel):
    id: UUID4


class GroupWithPhaseIdOut(BaseModel):
    id: UUID4
    code: str
    phase: Phase
    description: str

    @classmethod
    def from_instance(cls, group: "GroupModel", *, lang: Lang) -> "GroupWithPhaseIdOut":
        return cls(
            id=group.id,
            code=group.code,
            phase=Phase(id=group.phase_id),
            description=get_language_description(group, lang),
        )


class AllGroupsResponse(BaseModel):
    phases: list[PhaseOut]
    groups: list[GroupWithPhaseIdOut]


class GroupResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut


class GroupsByPhaseCodeResponse(BaseModel):
    phase: PhaseOut
    groups: list[GroupOut]
