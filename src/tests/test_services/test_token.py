import uuid

import httpx
import pytest
from fastapi import encoders
from passlib import context
from passlib.hash import bcrypt
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app import main
from app.models import auth as auth_models


@pytest.mark.asyncio
async def test_create_jwt_token_by_username_and_passowrd(
    client: httpx.AsyncClient,
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


@pytest.mark.asyncio
async def test_create_token_by_username_and_passowrd_hash(
    client: httpx.AsyncClient,
    migrate: None,
    db: sqlalchemy_asyncio.AsyncSession,
):
    pwd_context = context.CryptContext(schemes=["bcrypt"], deprecated="auto")

    username = str(uuid.uuid4())
    password = str(uuid.uuid4())
    password_hash = pwd_context.hash(password)
    r"""依照規格把資訊拆分出來
    $2a$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW
    \__/\/ \____________________/\_____________________________/
    Alg Cost      Salt                        Hash
    """
    alg, cost, salt_and_hash = password_hash.split("$")[1:]
    salt = salt_and_hash[:22]
    # 先測試可以手動產生相同 hash
    assert (
        bcrypt.using(
            ident=alg,
            rounds=cost,
            salt=salt,
        ).hash(password)
        == password_hash
    )
    # 將 hash 過後的密碼存到資料庫
    user_info = {
        "username": username,
        "password": password_hash,
    }
    obj_in_data = encoders.jsonable_encoder(user_info)
    user = auth_models.User(**obj_in_data)
    db.add(user)
    await db.commit()
    await db.flush()

    # 模擬前端
    # 先獲取 hash 資訊
    resp = await client.get(
        f"/v1/auth/users/hashes?username={username}",
    )
    assert resp.status_code == 200
    data = resp.json()
    alg, cost, salt = data["alg"], data["cost"], data["salt"]
    # 利用回傳回來的 hash 資訊做密碼 hash
    password_hash = bcrypt.using(
        ident=alg,
        rounds=cost,
        salt=salt,
    ).hash(password)
    # 真正做登入
    resp = await client.post(
        "/v1/auth/users/tokens",
        json={
            "username": username,
            "password": password_hash,
        },
    )
    assert resp.status_code == 200
