from pydantic import BaseModel, ConfigDict


class LogoOut(BaseModel):
    url: str

    model_config = ConfigDict(extra="forbid")


class CompetitionOut(BaseModel):
    code: str
    description: str
    logo: LogoOut

    model_config = ConfigDict(extra="forbid")
