from pydantic import UUID4, BaseModel, ConfigDict, constr


class LobbyOut(BaseModel):
    id: UUID4
    code: constr(min_length=2, max_length=10)

    model_config = ConfigDict(extra="forbid")


class LobbyIn(BaseModel):
    code: constr(min_length=2, max_length=10)

    model_config = ConfigDict(extra="forbid")
