from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class ApiEnvelope(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    data: dict | list | str | int | float | bool | None
    meta: dict
    error: dict | None
