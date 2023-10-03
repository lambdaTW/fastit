import pydantic


class LoginInfo(pydantic.BaseModel):
    username: str
    password: str


class UserInfo(LoginInfo):
    is_superuser: bool


class HashInfo(pydantic.BaseModel):
    alg: str
    cost: int
    salt: str
