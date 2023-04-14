from pydantic import UUID4, BaseModel, Extra


class SignupIn(BaseModel, extra=Extra.forbid):
    name: str
    first_name: str
    last_name: str
    password: str


class SignupOut(BaseModel, extra=Extra.forbid):
    id: UUID4
    name: str
    token: str


class LoginIn(BaseModel, extra=Extra.forbid):
    name: str
    password: str


class LoginOut(BaseModel, extra=Extra.forbid):
    id: UUID4
    name: str
    token: str


class CurrentUserOut(BaseModel):
    id: UUID4
    name: str

    class Config:
        orm_mode = True


class ModifyUserIn(BaseModel, extra=Extra.forbid):
    password: str
