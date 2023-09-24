import pydantic


class LoginInfo(pydantic.BaseModel):
    username: str
    password: str


class HashInfo(pydantic.BaseModel):
    alg: str
    cost: int
    salt: str
