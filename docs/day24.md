# 超級使用者 - 實作

老獅：盤點一下要做什麼吧

小獅：API 用來建立使用者

```
1. 超級使用者可建立一般使用者
2. 超級使用者可建立超級使用者
3. 一般使用者不能建立帳號密碼
```

老獅：很好，我們可以先建立一個 `fixture` 來建立超級使用者，並且建立其 `client`，讓我們更好寫更多測試


```python
# src/tests/test_services/test_users.py
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


async def test_superuser_can_create_user(
    client: httpx.AsyncClient,
    superuser_client: httpx.AsyncClient,
):
    username = str(uuid.uuid4())
    password = str(uuid.uuid4())
    user_info = {
        "username": username,
        "password": password,
        "is_superuser": False,
    }
    resp = await superuser_client.post("/v1/auth/users", json=user_info)
    assert resp.status_code == 201
    resp = await client.post(
        "/v1/auth/users/tokens",
        json=user_info,
    )
    assert resp.status_code == 200
```

```shell
make test
# 省略
                )
E               TypeError: 'is_superuser' is an invalid keyword argument for User

venv/lib/python3.8/site-packages/sqlalchemy/orm/decl_base.py:2134: TypeError
========================== 6 passed, 1 error in 3.10s ==========================
```
老獅：一如預期壞惹，我們來去加上欄位

```python
# src/app/models/auth.py
import sqlalchemy

from app.db import bases as model_bases


class User(model_bases.Base):
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    username = sqlalchemy.Column(sqlalchemy.String, index=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    is_superuser = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
```

```shell
make test
# 省略
E                   sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedColumnError'>: column "is_superuser" of relation "user" does not exist
E                   [SQL: INSERT INTO "user" (username, password, is_superuser) VALUES ($1::VARCHAR, $2::VARCHAR, $3::BOOLEAN) RETURNING "user".id]
E                   [parameters: ('username', 'password', False)]
E                   (Background on this error at: https://sqlalche.me/e/20/f405)

venv/lib/python3.8/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:802: ProgrammingError
```
小獅：沒有欄位。。。是為啥

老獅：我們在 `models` 上面增加了 `is_superuser` 但是資料庫內其實還是沒有，想想我們少了啥？

小獅：migrate!

老獅：你下看看啊

```shell
make migrate
/Users/super/project/fastit/src
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> b130fb2851db, add user table

make test
# 省略
E                   sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedColumnError'>: column "is_superuser" of relation "user" does not exist
E                   [SQL: INSERT INTO "user" (username, password, is_superuser) VALUES ($1::VARCHAR, $2::VARCHAR, $3::BOOLEAN) RETURNING "user".id]
E                   [parameters: ('username', 'password', False)]
E                   (Background on this error at: https://sqlalche.me/e/20/f405)

venv/lib/python3.8/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:802: ProgrammingError
```
小獅：怎麼還是錯一樣的

老獅：很明顯，你還沒搞清楚 migrate 是指，你要先有 `migration` 他依照 migration 的最終狀態去和資料庫比對以後幫你執行動作，你在 `models` 上面增加了欄位，但是你有產生出 `migration` 檔案惹嗎？

```shell
make migrations msg="add is_superuser flag"
/Users/super/project/fastit/src
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.ddl.postgresql] Detected sequence named 'user_id_seq' as owned by integer column 'user(id)', assuming SERIAL and omitting
INFO  [alembic.autogenerate.compare] Detected added column 'user.is_superuser'
  Generating /Users/super/project/fastit/src/app/migrations/versions/0d59755649aa_add_is_superuser_flag.py ...  done
```
```shell
make test
# 省略
E       assert 404 == 201
E        +  where 404 = <Response [404 Not Found]>.status_code

src/tests/test_services/test_users.py:53: AssertionError
```
小獅：好咧！開工！

```diff
+++ b/src/app/api/v1/routers.py
@@ -1,8 +1,10 @@
 import fastapi

+from app.api.v1.endpoints.auth.users import users as users_endpoints
 from app.api.v1.endpoints.auth.users import hashes as hashes_endpoints
 from app.api.v1.endpoints.auth.users import tokens as token_endpoints

 v1_router = fastapi.APIRouter()
+v1_router.include_router(users_endpoints.router, prefix="/auth/users")
 v1_router.include_router(token_endpoints.router, prefix="/auth/users/tokens")
 v1_router.include_router(hashes_endpoints.router, prefix="/auth/users/hashes")
```

```python
# src/app/api/v1/endpoints/auth/users/users.py
import fastapi

router = fastapi.APIRouter()


@router.post("", status_code=201)
async def create_user():
    return
```

```shell
make test
# 省略
        resp = await client.post(
            "/v1/auth/users/tokens",
            json=user_info,
        )
>       assert resp.status_code == 200
E       assert 401 == 200
E        +  where 401 = <Response [401 Unauthorized]>.status_code
```
小獅：想辦法讓他成功

```python
# src/app/schemas/users.py
class UserInfo(LoginInfo):
    is_superuser: bool
```

```python
# src/app/api/v1/endpoints/auth/users/users.py
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
```

```shell
make test
pytest .
============================= test session starts ==============================
platform darwin -- Python 3.8.13, pytest-7.4.0, pluggy-1.2.0
rootdir: /Users/super/project/fastit
configfile: pyproject.toml
plugins: asyncio-0.21.1, anyio-3.7.1
asyncio: mode=auto
collecting ... /Users/super/project/fastit/src
collected 7 items

src/tests/test_main.py .                                                 [ 14%]
src/tests/test_services/test_hashes.py .                                 [ 28%]
src/tests/test_services/test_token.py ...                                [ 71%]
src/tests/test_services/test_users.py .                                  [ 85%]
src/tests/test_units/test_users_crud.py .                                [100%]

============================== 7 passed in 3.17s ===============================
```

老獅：很好，提交後，接下來我們繼續處理其他測試的部分

```shell
git add src/app/api/v1/endpoints/auth/users/users.py
git add src/app/api/v1/routers.py
git add src/app/migrations/versions/0d59755649aa_add_is_superuser_flag.py
git add src/app/models/auth.py
git add src/app/schemas/users.py
git add src/tests/test_services/test_users.py
git commit -m "feat: add create user API"
```

## 本次目錄
```
.
├── Makefile
├── docker-compose.yml
├── pyproject.toml
├── requirements
│   ├── base.in
│   ├── base.txt
│   ├── development.in
│   └── development.txt
├── requirements.txt
├── setup.cfg
└── src
    ├── app
    │   ├── alembic.ini
    │   ├── api
    │   │   ├── dependencies.py
    │   │   └── v1
    │   │       ├── endpoints
    │   │       │   ├── __init__.py
    │   │       │   └── auth
    │   │       │       └── users
    │   │       │           ├── hashes.py
    │   │       │           ├── tokens.py
    │   │       │           └── users.py    # 新增
    │   │       └── routers.py              # 修改
    │   ├── crud
    │   │   └── auth.py
    │   ├── db
    │   │   ├── __init__.py
    │   │   └── bases.py
    │   ├── main.py
    │   ├── migrations
    │   │   ├── README
    │   │   ├── env.py
    │   │   ├── script.py.mako
    │   │   └── versions
    │   │       ├── 0d59755649aa_add_is_superuser_flag.py # 自動產生
    │   │       └── b130fb2851db_add_user_table.py
    │   ├── models
    │   │   └── auth.py    # 修改
    │   └── schemas
    │       ├── health_check.py
    │       ├── tokens.py
    │       └── users.py   # 修改
    ├── core
    │   └── config.py
    └── tests
        ├── conftest.py
        ├── test_main.py
        ├── test_services
        │   ├── test_hashes.py
        │   ├── test_token.py
        │   └── test_users.py    # 新增
        └── test_units
            └── test_users_crud.py
```
