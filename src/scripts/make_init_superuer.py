import asyncio

from passlib import context

from app.api import dependencies
from app.crud import auth as auth_crud
from core import config

settings = config.Settings()
pwd_context = context.CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_superuser():
    username = settings.INIT_SUPERUSER_USERNAME
    password = settings.INIT_SUPERUSER_PASSWORD
    password_hash = pwd_context.hash(password)
    obj_in = {"username": username, "password": password_hash, "is_superuser": True}
    async with dependencies.get_async_session_class(
        dependencies.get_db_engine(settings)
    )() as db:
        await auth_crud.user.create(db, obj_in)


asyncio.run(create_superuser())
