# 使用者驗證 - 測試不可知的事務以符合真實情境 - 2

小獅：搞了老半天，我們還是騙過去了

老獅：沒錯，因為我們測試還不夠全面，當我們納入第二項測試項目時，資料庫就必須進來了

小獅：`使用者 A 用錯密碼無法換取可以登入的 JWT token`，確實，這時候必須要驗證密碼，資料庫就是必需品了

```python
# src/tests/test_services/test_token.py
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
```

```shell
make test

=========================== short test summary info ============================
FAILED src/tests/test_services/test_token.py::test_user_cannot_get_jwt_token_by_incorrect_passowrd - assert 200 == 401
========================= 1 failed, 4 passed in 1.35s ==========================
make: *** [test] Error 1
```

老獅：一如預期的壞掉了，現在我們來讓他從資料庫撈取使用者資訊，再來比較密碼，首先我們先讓 `api` 可以拿到 `db`，我們使用 `FastAPI` 提供的 `Depends` 功能，並且將資料庫的 `dependency` 程式寫在 `dependencies.py`

```python
# src/app/api/dependencies.py
import functools

import fastapi
from sqlalchemy import orm
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from core import config

engine = None


@functools.lru_cache()
def get_settings() -> config.Settings:
    return config.Settings()


def get_db_engine(
    settings: config.Settings = fastapi.Depends(get_settings),
) -> sqlalchemy_asyncio.AsyncEngine:
    global engine
    engine = engine or sqlalchemy_asyncio.create_async_engine(
        settings.DATABASE_URL,
        echo=True,
    )
    return engine


def get_async_session_class(
    engine: sqlalchemy_asyncio.AsyncEngine = fastapi.Depends(get_db_engine),
) -> sqlalchemy_asyncio.AsyncSession:
    return orm.sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=sqlalchemy_asyncio.AsyncSession,
    )


async def get_db(
    async_session: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(
        get_async_session_class
    ),
) -> sqlalchemy_asyncio.AsyncSession:
    async with async_session() as session:
        yield session
```

老獅：這樣就可以用 `db` 來撈資料了

```python
# src/app/api/v1/endpoints/auth/users/tokens.py
from app.api import dependencies
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
from sqlalchemy import func as sqlalchemy_func


@router.post("", response_model=token_schemas.JWT)
def create_jtw_token(
    user: user_schemas.LoginInfo,
    db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
):
    user = (
        (
            await db.execute(
                sqlalchemy_future.select(auth_models.User).filter(
                    sqlalchemy_func.lower(auth_models.User.username)
                    == sqlalchemy_func.lower(login.username)
                    )
            )
        )
        .scalars()
        .first()
    )
    if user and login.password == user.password:
        access_token = create_access_token(dict(sub=user.username))
        refresh_token = create_access_token(dict(sub=user.username))
        return {"access_token": access_token, "refresh_token": refresh_token}
    raise fastapi.HTTPException(
        fastapi.status.HTTP_401_UNAUTHORIZED,
        {"msg": "Invliad username or password"}
    )
```

```shell
make test
# 省略
E                   sqlalchemy.exc.InterfaceError: (sqlalchemy.dialects.postgresql.asyncpg.InterfaceError) <class 'asyncpg.exceptions._base.InterfaceError'>: connection is closed
E                   [SQL: SELECT "user".id, "user".username, "user".password
E                   FROM "user"
E                   WHERE lower("user".username) = lower($1::VARCHAR)]
E                   [parameters: ('1a2a6295-95d9-45d7-96d5-55a101dd3c17',)]
E                   (Background on this error at: https://sqlalche.me/e/20/rvf5)

venv/lib/python3.8/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:802: InterfaceError
========================= 2 failed, 3 passed in 1.92s ==========================
```

小獅：這啥？

老獅：我猜應該是，測試中兩個不同的連線相互使用相同的 pool 導致的

小獅：所以我們怎麼讓他分開？

老獅：我們可以讓 `dependencies` 上面的 `pool` 指定為 `NullPool` 讓他不會和測試資料庫所使用的 Pool 一樣

```python
# src/app/api/dependencies.py
from sqlalchemy import pool


def get_db_engine(
    settings: config.Settings = fastapi.Depends(get_settings),
) -> sqlalchemy_asyncio.AsyncEngine:
    global engine
    engine = engine or sqlalchemy_asyncio.create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        poolclass=pool.NullPool,
    )
    return engine
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
collected 5 items

src/tests/test_main.py .                                                 [ 20%]
src/tests/test_services/test_token.py ..                                 [ 60%]
src/tests/test_units/test_old.py .                                       [ 80%]
src/tests/test_units/test_users_crud.py .                                [100%]

============================== 5 passed in 1.41s ===============================
```

老獅：很好我們提交吧

```shell
git add src/app/api/dependencies.py
git add src/app/api/v1/endpoints/auth/users/tokens.py
git add src/tests/test_services/test_token.py
git commit -m "feat: implement password validate" -m "test: user cannot get jwt token by incorrect passowrd"
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
    │   │   ├── dependencies.py    # 新增
    │   │   └── v1
    │   │       ├── endpoints
    │   │       │   └── auth
    │   │       │       └── users
    │   │       │           └── tokens.py    # 更改
    │   │       └── routers.py
    │   ├── crud
    │   ├── db
    │   │   └── bases.py
    │   ├── main.py
    │   ├── migrations
    │   │   ├── README
    │   │   ├── env.py
    │   │   ├── script.py.mako
    │   │   └── versions
    │   │       └── b130fb2851db_add_user_table.py
    │   ├── models
    │   │   └── auth.py
    │   └── schemas
    │       ├── health_check.py
    │       ├── tokens.py
    │       └── users.py
    ├── core
    │   └── config.py
    ├── scripts
    └── tests
        ├── conftest.py
        ├── test_main.py
        ├── test_services
        │   └── test_token.py    # 新增測試
        └── test_units
            └── test_users_crud.py
```
