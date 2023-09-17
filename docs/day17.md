# 使用者驗證 - 測試不可知的事務以符合真實情境 - 1

老獅：接下來我們就依照我們列出的項目開始實作測試，將原本的 `test_create_jwt_token_by_username_and_passowrd` 進行改寫，這邊我們使用 `uuid` 來幫我們產生亂數的帳號密碼，用以取代原本我們寫死的 `test` 帳號密碼，並且將其寫入資料庫

```python
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
```

```
make test
E       fixture 'migrate' not found
>       available fixtures: anyio_backend, anyio_backend_name, anyio_backend_options, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, doctest_namespace, event_loop, monkeypatch, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory
>       use 'pytest --fixtures [testpath]' for help on them.

/Users/super/project/fastit/src/tests/test_services/test_token.py:12
=========================== short test summary info ============================
ERROR src/tests/test_services/test_token.py::test_create_jwt_token_by_username_and_passowrd
========================== 3 passed, 1 error in 0.89s ==========================
make: *** [test] Error 1
```

老獅：我們可以看到他說 `migrate` 找不到在哪，因為我們 `migrate` 這個 `fixture` 目前是寫在 `src/tests/test_units/test_users_crud.py` 當中，我們要讓 `test_create_jwt_token_by_username_and_passowrd` 也可以使用

小獅：複製貼上？

老獅：當然不是，我們可以寫在 `src/tests/conftest.py` 當中，`pytest` 在執行前會先一個目錄一個目錄的 `conftest` 都先跑過，才跑該目錄的測試檔案，所以，我們只要寫在最上層，下面的測試都可以吃到他們

```python
# src/tests/conftest.py
import pathlib
import typing
from unittest import mock

import pytest
from sqlalchemy import orm
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
from sqlalchemy_utils import functions

from core import config


@pytest.fixture
def settings() -> typing.Iterator[config.Settings]:
    settings = config.Settings()
    settings.DATABASE_URL = settings.DATABASE_URL + "_test"
    settings.MODE = "test"
    with mock.patch("core.config.Settings") as Settings:
        Settings.return_value = settings
        yield settings


@pytest.fixture
async def gen_db(
    settings: config.Settings,
) -> None:
    engine = sqlalchemy_asyncio.create_async_engine(
        settings.DATABASE_URL,
        echo=True,
    )
    sessionmaker = orm.sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=sqlalchemy_asyncio.AsyncSession,
    )
    async with sessionmaker() as session:
        async with session as db:
            await db.run_sync(
                lambda _: (functions.create_database(settings.DATABASE_URL))
            )
            yield
        async with session as db:
            await db.close()
            await db.run_sync(
                lambda _: (functions.drop_database(settings.DATABASE_URL))
            )


@pytest.fixture
async def migrate(
    settings: config.Settings,
    gen_db: None,
) -> typing.AsyncIterator[None]:
    from alembic import config as alembic_config
    from alembic.runtime.environment import EnvironmentContext
    from alembic.script import ScriptDirectory

    alembic_cfg = alembic_config.Config(file_=str(pathlib.Path("src/app/alembic.ini")))
    alembic_cfg.set_main_option(
        "script_location", str(pathlib.Path("src/app/migrations"))
    )
    script = ScriptDirectory.from_config(alembic_cfg)

    def upgrade(rev, context):
        return script._upgrade_revs("heads", rev)

    context_kwargs = dict(
        config=alembic_cfg,
        script=script,
    )
    upgrade_kwargs = dict(fn=upgrade, starting_rev=None, destination_rev="heads")
    with EnvironmentContext(**upgrade_kwargs, **context_kwargs):
        from app.migrations import env

        await env.run_async_migrations()
        yield


@pytest.fixture
async def db(
    settings: config.Settings,
    gen_db: None,
) -> typing.AsyncIterator[sqlalchemy_asyncio.AsyncSession]:
    engine = sqlalchemy_asyncio.create_async_engine(
        settings.DATABASE_URL,
        echo=True,
    )
    sessionmaker = orm.sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=sqlalchemy_asyncio.AsyncSession,
    )
    async with sessionmaker() as session:
        async with session as db:
            yield db
```

```
make test
# ... 省略
>           assert resp.json()["username"] == username
E           AssertionError: assert 'test' == '5e5b182f-d41...-cacbd253fb76'
E             - 5e5b182f-d419-4703-a253-cacbd253fb76
E             + test

src/tests/test_services/test_token.py:43: AssertionError
```

老獅：很好，一如預期的壞了，我們寫死的是無法使用的，接下來我們就可以更改我們的程式令其符合測試，我們可以利用 `FastAPI` 提供的依賴注入，直接拿到請求的 HTTP Body 資料

```python
# src/app/schemas/users.py
import pydantic


class LoginInfo(pydantic.BaseModel):
    username: str
    password: str
```

老獅：這樣我們就可以把使用者帳號拿去建立 `access_token`，`refresh_token` 我們先不做任何事情，就讓他和 `access_token`

```python
# src/app/api/v1/endpoints/auth/users/tokens.py
from app.schemas import tokens as token_schemas
from app.schemas import users as user_schemas


@router.post("")
def create_jwt_token(
    user: user_schemas.LoginInfo,
):
    access_token = create_access_token(dict(sub=user.username))
    refresh_token = create_access_token(dict(sub=user.username))
    return {"access_token": access_token, "refresh_token": refresh_token}
```

老獅：老樣子，我們可以設定回傳的 `schema` 讓前端可以在 `docs` 頁面了解回傳的資訊

```python
# src/app/schemas/tokens.py
import pydantic


class JWT(pydantic.BaseModel):
    access_token: str
    refresh_token: str
```

```python
# src/app/api/v1/endpoints/auth/users/tokens.py
from app.schemas import tokens as token_schemas
from app.schemas import users as user_schemas


@router.post("", response_model=token_schemas.JWT)
def create_jwt_token(
    user: user_schemas.LoginInfo,
):
    access_token = create_access_token(dict(sub=user.username))
    refresh_token = create_access_token(dict(sub=user.username))
    return {"access_token": access_token, "refresh_token": refresh_token}
```

小獅：我們如何實作 `create_access_token`？

老獅：我們可以先簡單的給予 `token` 過期時間 (exp)，以及該 `token` 的 `subject` (sub) 這邊我們已經預設好，會使用使用者名稱，存在 `token` 中

小獅：如果我沒有記錯，`token` 內是不是不能放機敏資料？

老獅：對的，由於 `JWT` 在 `payload` 中僅僅只有編碼，而非加密，所以我們只能存使用者相關，但是相對不機敏的資料

```python
import datetime
from jose import jwt

from core import config


def create_access_token(
    data: dict, expires_delta: typing.Optional[datetime.timedelta] = None
):
    to_encode = data.copy()
    now = datetime.datetime.utcnow()
    expire = now + datetime.timedelta(minutes=15)
    if expires_delta:
        expire = now + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, config.Settings().authjwt_secret_key, algorithm="HS256"
    )
    return encoded_jwt
```

老獅：這邊我們就直接先寫死 `exp` 為 15 分鐘，演算法我們先給死 `HS256`，至於用來做 `HASH` 的密鑰，希望你還記得怎麼拿

```shell
make test
# ...省略
>           assert resp.json()["username"] == username
E           AssertionError: assert 'test' == 'df347bdd-5c6...-a6b04d6d3529'
E             - df347bdd-5c60-448d-a57c-a6b04d6d3529
E             + test

src/tests/test_services/test_token.py:43: AssertionError
```

老獅：很好，我們現在來改 token info 的 API，讓他從 `token` 中拿取 `username`，我們就用一樣的方式去解開 `token` 即可

```python
# src/app/api/v1/endpoints/auth/users/tokens.py
from fastapi import security


@router.get("/info")
def get_jwt_token_info(
    token: str = fastapi.Depends(security.OAuth2PasswordBearer(tokenUrl="token")),
):
    credentials_exception = fastapi.HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            config.Settings().authjwt_secret_key,
            algorithms=["HS256"],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jose.JWTError:
        raise credentials_exception

    return {"username": username}
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
collected 4 items

src/tests/test_main.py .                                                 [ 25%]
src/tests/test_services/test_token.py .                                  [ 50%]
src/tests/test_units/test_old.py .                                       [ 75%]
src/tests/test_units/test_users_crud.py .                                [100%]
============================== 4 passed in 1.12s ===============================
```

小獅：我們完全沒用到資料庫，也沒有對密碼耶 @@

老獅：沒錯，所以我們要寫更多測試來完善它，先提交吧

```shell
make lint-fix && make lint
git add  src/app/api/v1/endpoints/auth/users/tokens.py
git add  src/app/schemas/tokens.py
git add  src/app/schemas/users.py
git add  src/tests/conftest.py
git add  src/tests/test_services/test_token.py
git add  src/tests/test_units/test_users_crud.py
git commit -m "feat: implement generate and validate JWT"
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
    │   │   └── v1
    │   │       ├── endpoints
    │   │       │   └── auth
    │   │       │       └── users
    │   │       │           └── tokens.py  # 更新
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
    │       ├── tokens.py    # 新增
    │       └── users.py     # 新增
    ├── core
    │   └── config.py
    ├── scripts
    └── tests
        ├── conftest.py          # 新增
        ├── test_main.py
        ├── test_services
        │   └── test_token.py    # 更新
        └── test_units
            └── test_users_crud.py    # 拿掉共用的 fixtures
```
