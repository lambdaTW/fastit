# 超級使用者 - 初始化 Script - 實作

小獅：好，所以我們要想辦法可以實作一個 Script，並且可以用這指令去產生預設超級使用者

```shell
python3 src/scripts/make_init_superuer.py
```

老獅：我們可以試著直接寫個 `Python Script` 來執行

```python
# src/scripts/make_init_superuer.py
from core import config
from app.api import dependencies

settings = config.Settings()

username = settings.INIT_SUPERUSER_USERNAME
password = settings.INIT_SUPERUSER_PASSWORD
obj_in = {
    "username": username,
    "password": password,
    "is_superuser": True
}
db = await dependencies.get_db(
    dependencies.get_async_session_class(
        dependencies.get_db_engine(settings)
    )
)
await auth_crud.user.create(db, obj_in)
```

小獅：我的編輯器一堆線耶

老獅：表示我們寫法有點問題，我們先跑看看錯誤寫什麼

```shell
(fastit) $ python src/scripts/make_init_superuer.py
  File "/Users/super/projects/fastit/src/scripts/make_init_superuer.py", line 14
    db = await dependencies.get_db(
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
SyntaxError: 'await' outside function
```

小獅：`await` 只能在函式當中？

老獅：是的，而且還只能再有寫 `async` 的函式內，我們來改寫吧

```python
# src/scripts/make_init_superuer.py
from core import config
from app.api import dependencies
from app.crud import auth as auth_crud

settings = config.Settings()


async def create_superuser():
    username = settings.INIT_SUPERUSER_USERNAME
    password = settings.INIT_SUPERUSER_PASSWORD
    obj_in = {
        "username": username,
        "password": password,
        "is_superuser": True
    }
    db = await dependencies.get_db(
        dependencies.get_async_session_class(
            dependencies.get_db_engine(settings)
        )
    )
    await auth_crud.user.create(db, obj_in)
```

小獅：痾。。不是啊，這樣我們根本沒有執行啊

老獅：對的，所以我們要讓他，被執行，我們可以用 `asyncio.run` 來執行異步函式

```
import asyncio


asyncio.run(create_superuser())
```

```shell
(fastit) $ python src/scripts/make_init_superuer.py
/Users/super/projects/fastit/src
Traceback (most recent call last):
  File "/Users/super/projects/fastit/src/scripts/make_init_superuer.py", line 25, in <module>
    asyncio.run(create_superuser())
  File "/usr/local/Cellar/python@3.11/3.11.3/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/local/Cellar/python@3.11/3.11.3/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/Cellar/python@3.11/3.11.3/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/base_events.py", line 653, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/Users/super/projects/fastit/src/scripts/make_init_superuer.py", line 10, in create_superuser
    username = settings.INIT_SUPERUSER_USERNAME
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/super/projects/fastit/venv/lib/python3.11/site-packages/pydantic/main.py", line 726, in __getattr__
    raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
AttributeError: 'Settings' object has no attribute 'INIT_SUPERUSER_USERNAME'
```

小獅：恩，來補一下

```python
# src/core/config.py
import pathlib
import typing

import pydantic_settings

PROJECT_PATH = pathlib.Path(__file__).parent.parent
print(PROJECT_PATH)


class Settings(pydantic_settings.BaseSettings):
    authjwt_secret_key: str = "secret"
    DATABASE_URL: str
    MODE: typing.Literal["test", "development", "production"] = "development"
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=PROJECT_PATH / ".env",
        extra="ignore",
    )
    INIT_SUPERUSER_USERNAME: typing.Optional[str] = None
    INIT_SUPERUSER_PASSWORD: typing.Optional[str] = None
```

```shell
(fastit) $ python src/scripts/make_init_superuer.py
/Users/super/projects/fastit/src
Traceback (most recent call last):
  File "/Users/super/projects/fastit/src/scripts/make_init_superuer.py", line 25, in <module>
    asyncio.run(create_superuser())
  File "/usr/local/Cellar/python@3.11/3.11.3/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/usr/local/Cellar/python@3.11/3.11.3/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/Cellar/python@3.11/3.11.3/Frameworks/Python.framework/Versions/3.11/lib/python3.11/asyncio/base_events.py", line 653, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/Users/super/projects/fastit/src/scripts/make_init_superuer.py", line 17, in create_superuser
    db = await dependencies.get_db(
         ^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: object async_generator can't be used in 'await' expression
```

小獅：這又是啥？


老獅：我們 `get_db` 這邊是 `yield` 一個 session 出來，我們要讓他可以得到 `session`

```python
    async with dependencies.get_async_session_class(
        dependencies.get_db_engine(settings)
    )() as db:
        await auth_crud.user.create(db, obj_in)
```

```shell
python src/scripts/make_init_superuer.py
sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.NotNullViolationError'>: null value in column "password" of relation "user" violates not-null constraint
DETAIL:  Failing row contains (2, null, null, t).
[SQL: INSERT INTO "user" (username, password, is_superuser) VALUES ($1::VARCHAR, $2::VARCHAR, $3::BOOLEAN) RETURNING "user".id]
[parameters: (None, None, True)]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
```

小獅：所以我應該要塞一下，就可以動了吧！

```shell
export INIT_SUPERUSER_USERNAME=super
export INIT_SUPERUSER_PASSWORD=mysecretpassword

python src/scripts/make_init_superuer.py
2023-10-12 21:46:29,060 INFO sqlalchemy.engine.Engine select pg_catalog.version()
2023-10-12 21:46:29,060 INFO sqlalchemy.engine.Engine [raw sql] ()
2023-10-12 21:46:29,064 INFO sqlalchemy.engine.Engine select current_schema()
2023-10-12 21:46:29,064 INFO sqlalchemy.engine.Engine [raw sql] ()
2023-10-12 21:46:29,067 INFO sqlalchemy.engine.Engine show standard_conforming_strings
2023-10-12 21:46:29,067 INFO sqlalchemy.engine.Engine [raw sql] ()
2023-10-12 21:46:29,070 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2023-10-12 21:46:29,072 INFO sqlalchemy.engine.Engine INSERT INTO "user" (username, password, is_superuser) VALUES ($1::VARCHAR, $2::VARCHAR, $3::BOOLEAN) RETURNING "user".id
2023-10-12 21:46:29,072 INFO sqlalchemy.engine.Engine [generated in 0.00037s] ('super', 'mysecretpassword', True)
2023-10-12 21:46:29,081 INFO sqlalchemy.engine.Engine COMMIT
```

老獅：檢查一下資料庫吧！

```shell
(fastit) $ docker-compose exec postgres sh
/ # psql -U postgres
psql (13.2)
Type "help" for help.

postgres=# \c db
You are now connected to database "db" as user "postgres".
db=# select * from user;
   user
----------
 postgres
(1 row)

db=# select * from "user";
 id | username |     password     | is_superuser
----+----------+------------------+--------------
  3 | super    | mysecretpassword | t
(1 row)
```


小獅：這密碼好像不對，我們是不是應該要給他過個 hash

老獅：恩恩恩

```python
import asyncio
from core import config
from app.api import dependencies
from app.crud import auth as auth_crud
from passlib import context

settings = config.Settings()
pwd_context = context.CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_superuser():
    username = settings.INIT_SUPERUSER_USERNAME
    password = settings.INIT_SUPERUSER_PASSWORD
    password_hash = pwd_context.hash(password)
    obj_in = {
        "username": username,
        "password": password_hash,
        "is_superuser": True
    }
    async with dependencies.get_async_session_class(
        dependencies.get_db_engine(settings)
    )() as db:
        await auth_crud.user.create(db, obj_in)


asyncio.run(create_superuser())
```

```shell
python src/scripts/make_init_superuer.py
/Users/super/projects/fastit/src
2023-10-12 21:55:50,761 INFO sqlalchemy.engine.Engine select pg_catalog.version()
2023-10-12 21:55:50,761 INFO sqlalchemy.engine.Engine [raw sql] ()
2023-10-12 21:55:50,765 INFO sqlalchemy.engine.Engine select current_schema()
2023-10-12 21:55:50,765 INFO sqlalchemy.engine.Engine [raw sql] ()
2023-10-12 21:55:50,768 INFO sqlalchemy.engine.Engine show standard_conforming_strings
2023-10-12 21:55:50,768 INFO sqlalchemy.engine.Engine [raw sql] ()
2023-10-12 21:55:50,771 INFO sqlalchemy.engine.Engine BEGIN (implicit)
2023-10-12 21:55:50,772 INFO sqlalchemy.engine.Engine INSERT INTO "user" (username, password, is_superuser) VALUES ($1::VARCHAR, $2::VARCHAR, $3::BOOLEAN) RETURNING "user".id
2023-10-12 21:55:50,772 INFO sqlalchemy.engine.Engine [generated in 0.00018s] ('super', '$2b$12$7PP3TKU4RS2u7hRnxYc5Vu38GY.vV0gpn9TZjnTYM/qejRy0/ZwOW', True)
2023-10-12 21:55:50,777 INFO sqlalchemy.engine.Engine COMMIT
```


```shell
db=# select * from "user";
 id | username |                           password                           | is_superuser
----+----------+--------------------------------------------------------------+--------------
  3 | super    | mysecretpassword                                             | t
  4 | super    | $2b$12$7PP3TKU4RS2u7hRnxYc5Vu38GY.vV0gpn9TZjnTYM/qejRy0/ZwOW | t
```

老獅：很好，看起來好多了，我們先提交吧

```shell
make lint-fix && make lint

git add src/scripts/
git add src/core/config.py

git commit -m "feat: add create superuser script"
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
    │   │       │           └── users.py
    │   │       └── routers.py
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
    │   │       ├── 0d59755649aa_add_is_superuser_flag.py
    │   │       └── b130fb2851db_add_user_table.py
    │   ├── models
    │   │   └── auth.py
    │   └── schemas
    │       ├── health_check.py
    │       ├── tokens.py
    │       └── users.py
    ├── core
    │   └── config.py    # 新增欄位
    ├── scripts
    │   └── make_init_superuer.py  # 新增
    └── tests
        ├── conftest.py
        ├── test_main.py
        ├── test_services
        │   ├── test_hashes.py
        │   ├── test_token.py
        │   └── test_users.py
        └── test_units
            └── test_users_crud.py
```
