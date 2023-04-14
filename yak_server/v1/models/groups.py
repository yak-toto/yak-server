from typing import List

from pydantic import UUID4, BaseModel

from .phases import PhaseOut


class GroupIn(BaseModel):
    id: UUID4


class GroupOut(BaseModel):
    id: UUID4
    code: str
    description: str

    class Config:
        orm_mode = True


class Phase(BaseModel):
    id: UUID4

    class Config:
        orm_mode = True


class GroupWithPhaseIdOut(BaseModel):
    id: UUID4
    code: str
    phase: Phase
    description: str

    class Config:
        orm_mode = True


class AllGroupsResponse(BaseModel):
    phases: List[PhaseOut]
    groups: List[GroupWithPhaseIdOut]


class GroupResponse(BaseModel):
    phase: PhaseOut
    group: GroupOut


class GroupsByPhaseCodeResponse(BaseModel):
    phase: PhaseOut
    groups: List[GroupOut]
