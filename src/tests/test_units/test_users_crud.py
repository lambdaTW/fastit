import pytest
import sqlalchemy
from fastapi import encoders
from sqlalchemy import future as sqlalchemy_future
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app.models import auth as auth_models


@pytest.mark.asyncio
async def test_create_and_read_user(
    migrate: None,
    db: sqlalchemy_asyncio.AsyncSession,
):
    username = "username"
    password = "password"
    obj_in = {
        "username": username,
        "password": password,
    }
    await db.execute(sqlalchemy.text("select 1"))
    obj_in_data = encoders.jsonable_encoder(obj_in)
    user = auth_models.User(**obj_in_data)
    db.add(user)
    await db.commit()
    user = (
        (
            await db.execute(
                sqlalchemy_future.select(auth_models.User).where(
                    auth_models.User.id == user.id
                )
            )
        )
        .scalars()
        .first()
    )
    assert user.username == "username"
    assert user.password == "password"


# @pytest.mark.asyncio
# async def test_create_duplicated_user_will_raise_integrity_error(
#     migrate: None,
#     db: sqlalchemy_asyncio.AsyncSession,
# ):
#     username = "username"
#     password = "password"
#     obj_in = {
#         "username": username,
#         "password": password,
#     }
#     await db.execute(sqlalchemy.text("select 1"))
#     obj_in_data = encoders.jsonable_encoder(obj_in)
#     user_a = auth_models.User(**obj_in_data)
#     user_b = auth_models.User(**obj_in_data)
#     db.add(user_a)
#     await db.commit()
#     await db.flush()

#     with pytest.raises(db_exc.IntegrityError):
#         db.add(user_b)
#         await db.commit()
#         await db.flush()
