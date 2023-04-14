from pydantic import UUID4, BaseModel


class PhaseOut(BaseModel):
    id: UUID4
    code: str
    description: str

    class Config:
        orm_mode = True
