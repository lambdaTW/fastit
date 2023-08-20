import typing

import pydantic


class HealthResponse(pydantic.BaseModel):
    api: str
    version: typing.Optional[int] = None
