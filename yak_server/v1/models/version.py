from pydantic import BaseModel, ConfigDict


class VersionOut(BaseModel):
    version: str

    model_config = ConfigDict(extra="forbid")
