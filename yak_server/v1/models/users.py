from pydantic import UUID4, BaseModel, ConfigDict


class SignupIn(BaseModel):
    name: str
    first_name: str
    last_name: str
    password: str

    model_config = ConfigDict(extra="forbid")


class SignupOut(BaseModel):
    id: UUID4
    name: str
    access_token: str
    access_expires_in: int
    refresh_token: str
    refresh_expires_in: int

    model_config = ConfigDict(extra="forbid")


class PasswordRequirementsOut(BaseModel):
    minimum_length: int
    uppercase: bool
    lowercase: bool
    digit: bool
    no_space: bool

    model_config = ConfigDict(extra="forbid")


class LoginIn(BaseModel):
    name: str
    password: str

    model_config = ConfigDict(extra="forbid")


class LoginOut(BaseModel):
    id: UUID4
    name: str
    access_token: str
    access_expires_in: int
    refresh_token: str
    refresh_expires_in: int
    model_config = ConfigDict(extra="forbid")


class RefreshIn(BaseModel):
    refresh_token: str

    model_config = ConfigDict(extra="forbid")


class RefreshOut(BaseModel):
    access_token: str
    access_expires_in: int
    refresh_token: str
    refresh_expires_in: int

    model_config = ConfigDict(extra="forbid")


class CurrentUserOut(BaseModel):
    id: UUID4
    name: str

    model_config = ConfigDict(from_attributes=True)


class ModifyUserIn(BaseModel):
    password: str

    model_config = ConfigDict(extra="forbid")
