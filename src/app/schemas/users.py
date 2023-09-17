import pydantic


class LoginInfo(pydantic.BaseModel):
    username: str
    password: str
