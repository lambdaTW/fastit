from fastapi import encoders
from sqlalchemy import func as sqlalchemy_func
from sqlalchemy import future as sqlalchemy_future
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app.models import auth as auth_models


class CRUDUser:
    def __init__(self):
        self.model = auth_models.User

    async def create(self, db: sqlalchemy_asyncio.AsyncSession, obj_in: dict):
        obj_in_data = encoders.jsonable_encoder(obj_in)
        user = self.model(**obj_in_data)
        db.add(user)
        await db.commit()
        return user

    async def get_by_username(self, db: sqlalchemy_asyncio.AsyncSession, username: str):
        return (
            (
                await db.execute(
                    sqlalchemy_future.select(self.model).filter(
                        sqlalchemy_func.lower(self.model.username)
                        == sqlalchemy_func.lower(username)
                    )
                )
            )
            .scalars()
            .first()
        )


user = CRUDUser()
