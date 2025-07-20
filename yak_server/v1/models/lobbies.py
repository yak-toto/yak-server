from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, ConfigDict

if TYPE_CHECKING:
    from yak_server.database.models import LobbyModel, UserModel


class LobbyIn(BaseModel):
    name: str
    competition: str
    official_results_password: str

    model_config = ConfigDict(extra="forbid")


class LobbyOut(BaseModel):
    id: UUID4
    name: str

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_instance(cls, lobby: "LobbyModel") -> "LobbyOut":
        return cls(id=lobby.id, name=lobby.name)


class UserOut(BaseModel):
    id: UUID4
    name: str
    first_name: str
    last_name: str

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_instance(cls, user: "UserModel") -> "UserOut":
        return cls(id=user.id, name=user.name, first_name=user.first_name, last_name=user.last_name)


class LobbyOutWithUsers(LobbyOut):
    id: UUID4
    name: str
    users: list[UserOut]

    @classmethod
    def from_instance(cls, lobby: "LobbyModel") -> "LobbyOutWithUsers":
        users = [UserOut.from_instance(user) for user in lobby.users]
        return cls(id=lobby.id, name=lobby.name, users=users)
