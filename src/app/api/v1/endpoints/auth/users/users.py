import fastapi
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app.api import dependencies
from app.crud import auth as auth_crud
from app.schemas import users as users_schemas

router = fastapi.APIRouter()


@router.post("", status_code=201)
async def create_user(
    user_info: users_schemas.UserInfo = fastapi.Body(),
    db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
):
    user = await auth_crud.user.create(db, user_info)
    return user.__dict__
