from pydantic import BaseModel, ConfigDict


class VersionOut(BaseModel):
    version: str
    schema_hash: str

    model_config = ConfigDict(extra="forbid")
