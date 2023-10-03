import typing
import uuid

import httpx
import pytest
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app import main
from app.crud import auth as auth_crud
from app.models import auth as auth_models


@pytest.fixture
async def superuser(
    migrate: None, db: sqlalchemy_asyncio.AsyncSession
) -> auth_models.User:
    return await auth_crud.user.create(
        db,
        {
            "username": str(uuid.uuid4()),
            "password": str(uuid.uuid4()),
            "is_superuser": True,
        },
    )


@pytest.fixture
async def superuser_client(
    superuser: auth_models.User,
) -> typing.AsyncIterator[httpx.AsyncClient]:
    from app.api.v1.endpoints.auth.users import tokens

    async with httpx.AsyncClient(
        app=main.app,
        base_url="http://test",
    ) as async_client:
        token = tokens.create_access_token(dict(sub=superuser.username))
        async_client.headers = {"authorization": f"Bearer {token}"}
        yield async_client


@pytest.fixture
async def user(migrate: None, db: sqlalchemy_asyncio.AsyncSession) -> auth_models.User:
    return await auth_crud.user.create(
        db,
        {
            "username": str(uuid.uuid4()),
            "password": str(uuid.uuid4()),
            "is_superuser": False,
        },
    )


@pytest.fixture
async def user_client(
    user: auth_models.User,
) -> typing.AsyncIterator[httpx.AsyncClient]:
    from app.api.v1.endpoints.auth.users import tokens

    async with httpx.AsyncClient(
        app=main.app,
        base_url="http://test",
    ) as async_client:
        token = tokens.create_access_token(dict(sub=user.username))
        async_client.headers = {"authorization": f"Bearer {token}"}
        yield async_client


@pytest.mark.parametrize("is_superuser", [True, False])
async def test_superuser_can_create_user(
    db: sqlalchemy_asyncio.AsyncSession,
    client: httpx.AsyncClient,
    superuser_client: httpx.AsyncClient,
    is_superuser: bool,
):
    username = str(uuid.uuid4())
    password = str(uuid.uuid4())
    user_info = {
        "username": username,
        "password": password,
        "is_superuser": is_superuser,
    }
    resp = await superuser_client.post("/v1/auth/users", json=user_info)
    assert resp.status_code == 201
    resp = await client.post(
        "/v1/auth/users/tokens",
        json=user_info,
    )
    assert resp.status_code == 200
    user = await auth_crud.user.get_by_username(db, username)
    assert user.is_superuser is user_info["is_superuser"]


async def test_user_cannot_create_superuser(
    db: sqlalchemy_asyncio.AsyncSession,
    user_client: httpx.AsyncClient,
):
    username = str(uuid.uuid4())
    password = str(uuid.uuid4())
    user_info = {
        "username": username,
        "password": password,
        "is_superuser": True,
    }
    resp = await user_client.post("/v1/auth/users", json=user_info)
    assert resp.status_code == 403


async def test_anonymous_cannot_create_superuser(
    db: sqlalchemy_asyncio.AsyncSession,
    client: httpx.AsyncClient,
):
    username = str(uuid.uuid4())
    password = str(uuid.uuid4())
    user_info = {
        "username": username,
        "password": password,
        "is_superuser": True,
    }
    resp = await client.post("/v1/auth/users", json=user_info)
    assert resp.status_code == 401
