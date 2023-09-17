import uuid

import httpx
import pytest
from fastapi import encoders
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app import main
from app.models import auth as auth_models


@pytest.mark.asyncio
async def test_create_jwt_token_by_username_and_passowrd(
    migrate: None,
    db: sqlalchemy_asyncio.AsyncSession,
):
    username = str(uuid.uuid4())
    password = str(uuid.uuid4())
    user_info = {
        "username": username,
        "password": password,
    }
    obj_in_data = encoders.jsonable_encoder(user_info)
    user = auth_models.User(**obj_in_data)
    db.add(user)
    await db.commit()
    await db.flush()

    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.post(
            "/v1/auth/users/tokens",
            json=user_info,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert (access_token := data["access_token"])
        assert data["refresh_token"]
        resp = await client.get(
            "/v1/auth/users/tokens/info",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == username


@pytest.mark.asyncio
async def test_user_cannot_get_jwt_token_by_incorrect_passowrd(
    migrate: None,
    db: sqlalchemy_asyncio.AsyncSession,
):
    username = str(uuid.uuid4())
    password = str(uuid.uuid4())
    user_info = {
        "username": username,
        "password": password,
    }
    obj_in_data = encoders.jsonable_encoder(user_info)
    user = auth_models.User(**obj_in_data)
    db.add(user)
    await db.commit()
    await db.flush()
    user_info["password"] = "invalidpassword"

    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.post(
            "/v1/auth/users/tokens",
            json=user_info,
        )
        assert resp.status_code == 401
