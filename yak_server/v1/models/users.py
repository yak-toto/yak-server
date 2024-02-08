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
    token: str

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
    token: str

    model_config = ConfigDict(extra="forbid")


class CurrentUserOut(BaseModel):
    id: UUID4
    name: str

    model_config = ConfigDict(from_attributes=True)


class ModifyUserIn(BaseModel):
    password: str

    model_config = ConfigDict(extra="forbid")
