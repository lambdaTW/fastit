import datetime
import typing

import fastapi
import jose
from fastapi import security
from jose import jwt

from app.schemas import tokens as token_schemas
from app.schemas import users as user_schemas
from core import config

router = fastapi.APIRouter()


def create_access_token(
    data: dict, expires_delta: typing.Optional[datetime.timedelta] = None
):
    to_encode = data.copy()
    now = datetime.datetime.utcnow()
    expire = now + datetime.timedelta(minutes=15)
    if expires_delta:
        expire = now + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config.Settings().authjwt_secret_key, algorithm="HS256"
    )
    return encoded_jwt


@router.post("", response_model=token_schemas.JWT)
def create_jtw_token(
    user: user_schemas.LoginInfo,
):
    access_token = create_access_token(dict(sub=user.username))
    refresh_token = create_access_token(dict(sub=user.username))
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/info")
def get_jwt_token_info(
    token: str = fastapi.Depends(security.OAuth2PasswordBearer(tokenUrl="token")),
):
    credentials_exception = fastapi.HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            config.Settings().authjwt_secret_key,
            algorithms=["HS256"],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jose.JWTError:
        raise credentials_exception

    return {"username": username}
