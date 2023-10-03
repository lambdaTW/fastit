import fastapi
import jose
from fastapi import security
from jose import jwt
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app.api import dependencies
from app.crud import auth as auth_crud
from app.schemas import users as users_schemas
from core import config

router = fastapi.APIRouter()


@router.post("", status_code=201)
async def create_user(
    token: str = fastapi.Depends(security.OAuth2PasswordBearer(tokenUrl="token")),
    user_info: users_schemas.UserInfo = fastapi.Body(),
    db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
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
    action_user = await auth_crud.user.get_by_username(db, username)

    if not action_user.is_superuser:
        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_403_FORBIDDEN)
    user = await auth_crud.user.create(db, user_info)
    return user.__dict__
