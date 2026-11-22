from pydantic import BaseModel


class VersionOut(BaseModel):
    version: str
    schema_hash: str
