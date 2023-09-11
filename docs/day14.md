# 使用測試資料庫

## 資料遺留問題

```shell
make test
...
```

```shell
db=# select * from "user";
  1 | username | password
  2 | username | password
```

小獅：好像。。。會一直重複寫入資料？

老獅：沒錯，不只如此，現在是因為我們只有一個測試會使用到資料庫，想想看，如果你有兩個測試都寫入相同的資料，你又設定該資料是唯一的 (Unique) 時，會發生什麼事情

小獅：寫完第一筆資料以後所有測試都一定跑不過，那怎麼辦，手動刪除可以嗎？

老獅：你想刪到民國幾年？給點建設性的

小獅：我們可以每次都建立新的資料庫，給不同的測試使用

老獅：雖然會慢了一點，但是目前我們沒有效能問題，就先這樣做吧！

## 分離測試資料庫與開發資料庫
老獅：首先，我們為了留存自己手動測試使用的資料庫資料，先來把測試的資料庫與開發用的資料庫分開來，我們就簡單的在原本的資料庫後面加上 `_test` 來當作測試用的資料庫

```python
# src/tests/test_units/test_users_crud.py
@pytest.fixture
def settings() -> typing.Iterator[config.Settings]:
    settings = config.Settings()
    settings.DATABASE_URL = settings.DATABASE_URL + "_test"
    with mock.patch("core.config.Settings") as Settings:
        Settings.return_value = settings
        yield settings
```

```shell
make test
# 省略...

E               asyncpg.exceptions.InvalidCatalogNameError: database "db_test" does not exist

../../.pyenv/versions/3.8.13/lib/python3.8/asyncio/tasks.py:494: InvalidCatalogNameError
=========================== short test summary info ============================
FAILED src/tests/test_units/test_users_crud.py::test_create_and_read_user - asyncpg.exceptions.InvalidCatalogNameError: database "db_test" does not exist
========================= 1 failed, 3 passed in 1.02s ==========================
```
老獅：很好，他現在去要 `db_test` 這個資料庫了

## 自動建立與刪除資料庫
### sqlalchemy-utils
小獅：所以我們要在 `yield db` 以前建立資料庫，`CREATE DATABASE` 這簡單，我會

老獅：別衝動，我們這邊可以靠 `sqlalchemy-utils` 來產生對應的語法

小獅：喔，也是為了可以因應不同資料庫轉換的問題嗎？

老獅：沒錯，來安裝吧

```txt
fastapi==0.101.1
uvicorn[standard]==0.23.2
fastapi-jwt-auth==0.5.0
pydantic-settings==2.0.3
sqlalchemy[asyncio]==2.0.20
asyncpg==0.28.0
alembic==1.12.0
sqlalchemy-utils==0.41.1
```

```shell
make pip
```

### 建立測試資料庫
老獅：接下來我們就可以來建立他了，當然，跑完測試我們就把它刪掉，記得使用它

```python
# src/tests/test_units/test_users_crud.py
from sqlalchemy_utils import functions


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
async def db(
    settings: config.Settings,
    # 使用 gen_db
    gen_db: None,
) -> typing.AsyncIterator[sqlalchemy_asyncio.AsyncSession]:
    # 省略
```

```shell
make test

...省略
>                   raise translated_error from error
E                   sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedTableError'>: relation "user" does not exist
E                   [SQL: INSERT INTO "user" (username, password) VALUES ($1::VARCHAR, $2::VARCHAR) RETURNING "user".id]
E                   [parameters: ('username', 'password')]
E                   (Background on this error at: https://sqlalche.me/e/20/f405)

venv/lib/python3.8/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:802: ProgrammingError
```

老獅：可以看到現在回歸到沒有資料表的錯誤了

小獅：再來就是做 `migrate` 對吧

老獅：沒錯

## 測試前自動做 migrate 到測試資料庫

老獅：我們的目標就是 `src/app/migrations/env.py` 中 `do_run_migrations`，只要讓他在測試前跑過，我們要的資料表就應該要產生，當然，你要先做出最新版本的 `migration` 檔案，不過這邊就先假定你都會記得

```python
@pytest.fixture
async def migrate(
    settings: config.Settings,
    gen_db: None,
) -> typing.AsyncIterator[None]:
    from alembic import config as alembic_config
    from alembic.runtime.environment import EnvironmentContext
    from alembic.script import ScriptDirectory

    # 強制指定 alembic.ini
    alembic_cfg = alembic_config.Config(file_=str(pathlib.Path("src/app/alembic.ini")))
    # 強制指定 migrations 的資料夾
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
        # 跑起來！
        await env.run_async_migrations()
        yield


@pytest.mark.asyncio
async def test_create_and_read_user(
    # 記得使用喔！
    migrate: None,
    db: sqlalchemy_asyncio.AsyncSession,
):
```

```shell
make test
# 省略
        with EnvironmentContext(**upgrade_kwargs, **context_kwargs):
>           from app.migrations import env
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
src/app/migrations/env.py:100: in <module>
    run_migrations_online()
src/app/migrations/env.py:92: in run_migrations_online
    asyncio.run(run_async_migrations())
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

# 省略
        if events._get_running_loop() is not None:
>           raise RuntimeError(
                "asyncio.run() cannot be called from a running event loop")
E           RuntimeError: asyncio.run() cannot be called from a running event loop

../../.pyenv/versions/3.8.13/lib/python3.8/asyncio/runners.py:33: RuntimeError
```

小獅：`import env` 他幹嘛跑去執行 `run_migrations_online`?

老獅：因為他原本設定是 `import` 時就去跑，這樣當作 `script` 來用，我們把它改掉，當測試時不會跑

小獅：怎麼做？

老獅：我們可以指定程式的 `MODE` 然後，他不是有用到我們的 `Settings` 嗎？

小獅：恩？把 `MODE` 塞在 `Settings` 然後用它當 `flag`？

老獅：沒錯

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
```

```python
# src/app/migrations/env.py
# 省略請拉到最下面

if context.is_offline_mode():
    run_migrations_offline()
# 如果 MODE == "test" 就啥都不做
elif core_config.Settings().MODE == "test":
    pass
else:
    run_migrations_online()
```

```python
# src/tests/test_units/test_users_crud.py
@pytest.fixture
def settings() -> typing.Iterator[config.Settings]:
    settings = config.Settings()
    settings.DATABASE_URL = settings.DATABASE_URL + "_test"
    settings.MODE = "test"
    with mock.patch("core.config.Settings") as Settings:
        Settings.return_value = settings
        yield settings
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

============================== 4 passed in 0.88s ===============================
```

小獅：耶！可以提交拉！

```shell
git add src/tests/test_units/test_users_crud.py
git add requirements/base.in
git add requirements/base.txt
git add src/app/migrations/env.py
git add src/core/config.py
git m "test: user CRUD"
```

## 本次目錄
```
.
├── Makefile
├── docker-compose.yml
├── fake_pytest.py
├── pyproject.toml
├── requirements
│   ├── base.in     # 修改
│   ├── base.txt    # 修改
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
    │   │       │           └── tokens.py
    │   │       └── routers.py
    │   ├── crud
    │   ├── db
    │   │   └── bases.py
    │   ├── main.py
    │   ├── migrations
    │   │   ├── README
    │   │   ├── env.py    # 修改
    │   │   ├── script.py.mako
    │   │   └── versions
    │   │       └── b130fb2851db_add_user_table.py
    │   ├── models
    │   │   └── auth.py
    │   └── schemas
    │       └── health_check.py
    ├── core
    │   └── config.py    # 修改
    ├── scripts
    └── tests
        ├── test_main.py
        ├── test_services
        │   └── test_token.py
        └── test_units
            └── test_users_crud.py    # 新增
```
