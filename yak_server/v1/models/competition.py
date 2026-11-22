from pydantic import BaseModel


class LogoOut(BaseModel):
    url: str


class CompetitionOut(BaseModel):
    code: str
    description: str
    logo: LogoOut
