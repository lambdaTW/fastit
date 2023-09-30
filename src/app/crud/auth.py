from fastapi import encoders
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


user = CRUDUser()
