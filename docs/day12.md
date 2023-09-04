# 使用者驗證 - 測試儲存使用者資訊 - 除錯

小獅：套件裝好了，要先提交嗎？

老獅：等測試跑過我們再來提交吧

```shell
make test

==================================== ERRORS ====================================
___________ ERROR collecting src/tests/test_units/test_users_crud.py ___________
ImportError while importing test module '/Users/super/project/fastit/src/tests/test_units/test_users_crud.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../.pyenv/versions/3.8.13/lib/python3.8/importlib/__init__.py:127: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
src/tests/test_units/test_users_crud.py:6: in <module>
    from app.models import auth as auth_models
E   ImportError: cannot import name 'auth' from 'app.models' (unknown location)
=========================== short test summary info ============================
ERROR src/tests/test_units/test_users_crud.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
=============================== 1 error in 0.56s ===============================
make: *** [test] Error 2
```

老獅：我們需要 `models.auth.py` 去定義該表需要有的資料

```python
# src/app/models/auth.py

import typing

import sqlalchemy
from sqlalchemy import orm


@orm.as_declarative()
class Base:
    id: typing.Any
    __name__: str

    # Generate __tablename__ automatically
    @orm.declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class User(Base):
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    username = sqlalchemy.Column(sqlalchemy.String, index=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
```

```shell
make test
==================================== ERRORS ====================================
_________________ ERROR at setup of test_create_and_read_user __________________
file /Users/super/project/fastit/src/tests/test_units/test_users_crud.py, line 11
  @pytest.mark.asyncio
  async def test_create_and_read_user(
      db: sqlalchemy_asyncio.AsyncSession,
  ):
      username = "username"
      password = "password"
      obj_in = {
          "username": username,
          "password": password,
      }
      obj_in_data = encoders.jsonable_encoder(obj_in)
      obj = auth_models.User(**obj_in_data)
      db.add(obj)
      db.add(obj)
      user = await db.commit()
      user = (
          (
              await db.execute(
                  sqlalchemy_future.select(
                      auth_models.User
                  ).where(
                      auth_models.User.id == id
                  )
              )
          )
          .scalars()
          .first()
      )
      assert user.username == "username"
      assert user.password == "password"
E       fixture 'db' not found
>       available fixtures: anyio_backend, anyio_backend_name, anyio_backend_options, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, doctest_namespace, event_loop, monkeypatch, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory
>       use 'pytest --fixtures [testpath]' for help on them.

/Users/super/project/fastit/src/tests/test_units/test_users_crud.py:11
=========================== short test summary info ============================
ERROR src/tests/test_units/test_users_crud.py::test_create_and_read_user
========================== 2 passed, 1 error in 0.51s ==========================
make: *** [test] Error 1
```

老獅：很好，現在我們缺少資料庫的連線資訊，我們把他補上

```python
# src/tests/test_units/test_users_crud.py
import typing

import pytest

from fastapi import encoders
from sqlalchemy import orm
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
from sqlalchemy import future as sqlalchemy_future

from app.models import auth as auth_models


@pytest.fixture
async def db() -> typing.AsyncIterator[None]:
    engine = sqlalchemy_asyncio.create_async_engine(
        "postgresql+asyncpg://postgres@localhost:5432/db",
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
    await session.close()


@pytest.mark.asyncio
async def test_create_and_read_user(
    db: sqlalchemy_asyncio.AsyncSession,
):
    username = "username"
    password = "password"
    obj_in = {
        "username": username,
        "password": password,
    }
    obj_in_data = encoders.jsonable_encoder(obj_in)
    obj = auth_models.User(**obj_in_data)
    db.add(obj)
    user = await db.commit()
    user = (
        (
            await db.execute(
                sqlalchemy_future.select(
                    auth_models.User
                ).where(
                    auth_models.User.id == id
                )
            )
        )
        .scalars()
        .first()
    )
    assert user.username == "username"
    assert user.password == "password"
```

```shell
make test
pytest .
============================= test session starts ==============================
platform darwin -- Python 3.8.13, pytest-7.4.0, pluggy-1.2.0
rootdir: /Users/super/project/fastit
plugins: asyncio-0.21.1, anyio-3.7.1
asyncio: mode=strict
collected 3 items

src/tests/test_main.py .                                                 [ 33%]
src/tests/test_services/test_token.py .                                  [ 66%]
src/tests/test_units/test_users_crud.py F                                [100%]

=================================== FAILURES ===================================
__________________________ test_create_and_read_user ___________________________

db = <async_generator object db at 0x10f1b4550>

    @pytest.mark.asyncio
    async def test_create_and_read_user(
        db: sqlalchemy_asyncio.AsyncSession,
    ):
        username = "username"
        password = "password"
        obj_in = {
            "username": username,
            "password": password,
        }
        obj_in_data = encoders.jsonable_encoder(obj_in)
        obj = auth_models.User(**obj_in_data)
>       db.add(obj)
E       AttributeError: 'async_generator' object has no attribute 'add'

src/tests/test_units/test_users_crud.py:46: AttributeError
=============================== warnings summary ===============================
src/app/models/auth.py:7
  /Users/super/project/fastit/src/app/models/auth.py:7: MovedIn20Warning: The ``as_declarative()`` function is now available as sqlalchemy.orm.as_declarative() (deprecated since: 2.0) (Background on SQLAlchemy 2.0 at: https://sqlalche.me/e/b8d9)
    @declarative.as_declarative()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED src/tests/test_units/test_users_crud.py::test_create_and_read_user - AttributeError: 'async_generator' object has no attribute 'add'
==================== 1 failed, 2 passed, 1 warning in 0.53s ====================
make: *** [test] Error 1
```

小獅：What the F.. failure

老獅：恩，看起來異步 (async) 的 fixture 沒有正確被執行，被當作一般的 fixture 執行了，我們需要把 `pytest-async` 自動模式打開

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--asyncio-mode=auto"

[tool.black]
line-length = 88
exclude = '''
/(
  | venv
)/
'''

[tool.isort]
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
extend_skip = [
    "venv",
]
```

```shell
make test

...省略
E       ModuleNotFoundError: No module named 'asyncpg'

venv/lib/python3.8/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:1054: ModuleNotFoundError
=============================== warnings summary ===============================
src/app/models/auth.py:7
  /Users/super/project/fastit/src/app/models/auth.py:7: MovedIn20Warning: The ``as_declarative()`` function is now available as sqlalchemy.orm.as_declarative() (deprecated since: 2.0) (Background on SQLAlchemy 2.0 at: https://sqlalche.me/e/b8d9)
    @declarative.as_declarative()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR src/tests/test_units/test_users_crud.py::test_create_and_read_user - ModuleNotFoundError: No module named 'asyncpg'
==================== 2 passed, 1 warning, 1 error in 0.58s =====================
make: *** [test] Error 1
```

老獅：依照不同的資料庫連線，我們需要安裝對應的資料庫連線套件，在連線字串上，我們選用 `asyncpg` 所以這邊要裝一下他

小獅：所以我如果要用 `mysql` 是不是這邊改掉，就可以測試說有沒有安裝該套件？

老獅：對的，先寫好測試程式，可以依照需求去更改

```txt
# requirements/base.in
fastapi==0.101.1
uvicorn[standard]==0.23.2
fastapi-jwt-auth==0.5.0
pydantic-settings==2.0.3
sqlalchemy[asyncio]==2.0.20
asyncpg==0.28.0
```

```shell
make pip
```

```shell
make test
...省略
E                   OSError: Multiple exceptions: [Errno 61] Connect call failed ('127.0.0.1', 5432), [Errno 61] Connect call failed ('::1', 5432, 0, 0)

../../.pyenv/versions/3.8.13/lib/python3.8/asyncio/base_events.py:1033: OSError
=============================== warnings summary ===============================
src/app/models/auth.py:7
  /Users/super/project/fastit/src/app/models/auth.py:7: MovedIn20Warning: The ``as_declarative()`` function is now available as sqlalchemy.orm.as_declarative() (deprecated since: 2.0) (Background on SQLAlchemy 2.0 at: https://sqlalche.me/e/b8d9)
    @declarative.as_declarative()

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED src/tests/test_units/test_users_crud.py::test_create_and_read_user - OSError: Multiple exceptions: [Errno 61] Connect call failed ('127.0.0.1', ...
==================== 1 failed, 2 passed, 1 warning in 1.86s ====================
make: *** [test] Error 1
```

小獅：我知道，要起一個可以連線的 PostgreSQL，除了帳號密碼以外，連資料庫都要建立起來

老獅：那你知道怎麼讓開發人員方便使用嗎？

小獅：No

老獅：我們可以用環境變數組出連線字串，然後分別給 docker-compose 和程式可以使用到，並且寫到 `Makefile` 讓開發人員可以快速建立測試環境

小獅：願聞其詳

老獅：先試著手動建立 docker-compose 給測試使用，由於是給測試使用的，我們可以大量使用 ramdisk 來做加速，也不用讓資料真的寫入到硬碟內 `(fsync=off)`

```yml
version: '3.6'

services:
  postgres:
    restart: always
    image: postgres:13.2-alpine
    command: -c fsync=off
    ports:
      - "5432:5432"
    environment:
      - PGDATA=/pgtmpfs
    env_file:
      - src/.env
    volumes:
      - pg_vol:/pgtmpfs

volumes:
  pg_vol:
    driver_opts:
      type: tmpfs
      device: tmpfs
```

老獅：我們將 `.env` 檔案指定與我們 `pydantic-settings` 吃同一個檔案，接下來我們來更新他

```
# src/.env
authjwt_secret_key=thisismynewsecret
POSTGRES_HOST_AUTH_METHOD=scram-sha-256
POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgrespassword
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/db
```

老獅：我們試著將它開起來

```shell
docker-compoes up -d
```

```shell
make test

...省略
E               asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"

../../.pyenv/versions/3.8.13/lib/python3.8/asyncio/tasks.py:494: InvalidPasswordError
=========================== short test summary info ============================
FAILED src/tests/test_units/test_users_crud.py::test_create_and_read_user - asyncpg.exceptions.InvalidPasswordError: password authentication failed for...
========================= 1 failed, 2 passed in 0.97s ==========================
make: *** [test] Error 1
```

小獅：恩，測試檔案的密碼不一樣

老獅：我們可以改用環境變數去拿

```python
# src/core/config.py
import pathlib

import pydantic_settings

PROJECT_PATH = pathlib.Path(__file__).parent.parent
print(PROJECT_PATH)


class Settings(pydantic_settings.BaseSettings):
    authjwt_secret_key: str = "secret"
    DATABASE_URL: str
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=PROJECT_PATH / ".env",
    )

```

```python
# src/tests/test_units/test_users_crud.py
import typing

import pytest

from fastapi import encoders
from sqlalchemy import orm
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
from sqlalchemy import future as sqlalchemy_future

from app.models import auth as auth_models
from core import config


@pytest.fixture
def settings() -> config.Settings:
    return config.Settings()


@pytest.fixture
async def db(settings: config.Settings) -> typing.AsyncIterator[None]:
    engine = sqlalchemy_asyncio.create_async_engine(
        "postgresql+asyncpg://postgres@localhost:5432/db",
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
    await session.close()


@pytest.mark.asyncio
async def test_create_and_read_user(
    db: sqlalchemy_asyncio.AsyncSession,
):
    username = "username"
    password = "password"
    obj_in = {
        "username": username,
        "password": password,
    }
    obj_in_data = encoders.jsonable_encoder(obj_in)
    obj = auth_models.User(**obj_in_data)
    db.add(obj)
    user = await db.commit()
    user = (
        (
            await db.execute(
                sqlalchemy_future.select(
                    auth_models.User
                ).where(
                    auth_models.User.id == id
                )
            )
        )
        .scalars()
        .first()
    )
    assert user.username == "username"
    assert user.password == "password"
```

```shell
make test
...省略
E       pydantic_core._pydantic_core.ValidationError: 7 validation errors for Settings
E       postgres_host_auth_method
E         Extra inputs are not permitted [type=extra_forbidden, input_value='scram-sha-256', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.2/v/extra_forbidden
E       postgres_initdb_args
E         Extra inputs are not permitted [type=extra_forbidden, input_value='--auth-host=scram-sha-256', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.2/v/extra_forbidden
E       postgres_host
E         Extra inputs are not permitted [type=extra_forbidden, input_value='postgres', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.2/v/extra_forbidden
E       postgres_port
E         Extra inputs are not permitted [type=extra_forbidden, input_value='5432', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.2/v/extra_forbidden
E       postgres_db
E         Extra inputs are not permitted [type=extra_forbidden, input_value='db', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.2/v/extra_forbidden
E       postgres_user
E         Extra inputs are not permitted [type=extra_forbidden, input_value='postgres', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.2/v/extra_forbidden
E       postgres_password
E         Extra inputs are not permitted [type=extra_forbidden, input_value='postgrespassword', input_type=str]
E           For further information visit https://errors.pydantic.dev/2.2/v/extra_forbidden

venv/lib/python3.8/site-packages/pydantic_settings/main.py:71: ValidationError
=========================== short test summary info ============================
ERROR src/tests/test_units/test_users_crud.py::test_create_and_read_user - pydantic_core._pydantic_core.ValidationError: 7 validation errors for Settings
========================== 2 passed, 1 error in 0.58s ==========================
make: *** [test] Error 1
```

小獅：也太多錯誤訊息了吧，好像是多給了資料？但是我們 docker-compose 要用捏

老獅：預設 `pydantic_settings.BaseSettings` 不讓你喂沒有寫在欄位裡的資料進來，我們這邊更改他的設定，讓他忽略那些多設定的東西

```python
# src/core/config.py
import pathlib

import pydantic_settings

PROJECT_PATH = pathlib.Path(__file__).parent.parent
print(PROJECT_PATH)


class Settings(pydantic_settings.BaseSettings):
    authjwt_secret_key: str = "secret"
    DATABASE_URL: str
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=PROJECT_PATH / ".env",
        extra='ignore',
    )
```

```shell
make test
...省略
E                   sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedTableError'>: relation "user" does not exist
E                   [SQL: INSERT INTO "user" (username, password) VALUES ($1::VARCHAR, $2::VARCHAR) RETURNING "user".id]
E                   [parameters: ('username', 'password')]
E                   (Background on this error at: https://sqlalche.me/e/20/f405)

venv/lib/python3.8/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:802: ProgrammingError
```

小獅：看起來我們已經成功連上資料庫了，但是沒有資料表

老獅：沒錯，現在我們先把 `docker-compose.yml` 提交吧！順便改寫一下 `.env.example`

```
# .env.example
# For docker-compose PostgreSQL
POSTGRES_HOST_AUTH_METHOD=scram-sha-256
POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgrespassword

# For pydantic_settings
authjwt_secret_key=thisismynewsecret
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/db
```

```shell
git add docker-compose.yml
git add .env.example

git commit -m "chore: add test database" -m "docs: update .env.example"
```

老獅：`config` 也順便提交吧，後面也都用得到

```shell
git add src/core/config.py
git commit -m "feat: add the database config"
```

## 本次目錄
```
.
├── Makefile
├── pyproject.toml  # 修改，尚未提交
├── requirements
│   ├── base.in     # 修改，尚未提交
│   ├── base.txt    # 修改，尚未提交
│   ├── development.in
│   └── development.txt    # 修改，尚未提交
├── requirements.txt
├── setup.cfg
└── src
    ├── app
    │   ├── api
    │   │   └── v1
    │   │       ├── endpoints
    │   │       │   └── auth
    │   │       │       └── users
    │   │       │           └── tokens.py
    │   │       └── routers.py
    │   ├── crud
    │   ├── db
    │   ├── main.py
    │   ├── migrations
    │   ├── models
    │   │   └── auth.py    # 新增，尚未提交
    │   └── schemas
    │       └── health_check.py
    ├── core
    │   └── config.py
    ├── scripts
    └── tests
        ├── test_main.py
        ├── test_services
        │   └── test_token.py
        └── test_units
            └── test_users_crud.py    # 新增，尚未提交
```
