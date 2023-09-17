import pydantic


class JWT(pydantic.BaseModel):
    access_token: str
    refresh_token: str
