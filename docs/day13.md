# Migration (遷移)
小獅：我們將如何產生資料表？下 SQL 嗎？

老獅：我們已經有用 `python` 定義好了資料表的長相，在 `src/app/models/auth.py` 還記得嗎？

小獅：有喔，有點簡單，所以他可以產出資料表嗎？

老獅：他不行直接產生，我們可以另外使用做 migration 的工具，他就可以依照資料庫目前的狀態，去比對你寫好的 python model 然後將其差異動態產出對應的 SQL

小獅：所以。。。我加上一個新欄位，就會幫我 `ALTER TABLE` 囉？

老獅：不僅如此，如果你換資料庫，各個資料庫很多語法都不同，由於他是產出 `python` 檔案，最後在你做 `migrate` 時才依照你給予的資料庫引擎去產生相對的語法，所以在有換資料庫，或是多資料庫需求時，可以給我們很大的幫助

小獅：migrate?

老獅：migrate 的意思就是把 python 定義好的 model 同步到資料庫

小獅：那麼強喔，通通都可以自動處理嗎？

老獅：也不是這麼說，大部分簡單的案例可以，當然凡是有特例，特例就要靠你自己處理了

## 安裝 Migration 工具

老獅：來安裝吧，`alembic` 這套件可以依照 `sqlalchemy` 的 model 產生相對應的 `migration` 檔案，並且 `migrate` 他到真實資料庫

小獅：`migration` 檔案？

老獅：對的，此檔案就是剛剛說自動產出的 `python` 檔案，他會更接近 `SQL` 語法

小獅：好喔，裝東西我最會惹

```txt
# base.in
fastapi==0.101.1
uvicorn[standard]==0.23.2
fastapi-jwt-auth==0.5.0
pydantic-settings==2.0.3
sqlalchemy[asyncio]==2.0.20
asyncpg==0.28.0
alembic==1.12.0
```

```shell
make pip
```

## 初始化 alembic
老獅：裝好以後我們還要幹點事情

小獅：啥事情？

老獅：他需要初始化一些檔案，讓他後面可以做事情，我們依照[官方文件](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)的說明，來初始化他們，別忘了我們的目錄架構，輸入以下指令，會產生 `src/app/alembic.ini` 這個檔案以及 `src/app/migrations` 這個資料夾

```
cd src/app && alembic init --template async ./migrations
```

## 更新 alembic 設定
老獅：很讚，但是這樣他會吃到的資料庫 `URL` 會是 `driver://user:pass@localhost/dbname`

小獅：有辦法改嗎？

老獅：有的，他設定寫在 `src/app/alembic.ini` 這個檔案

小獅：改成 `postgresql+asyncpg://postgres@localhost:5432/db` 就好了吧？

老獅：可以，但是這樣你密碼不就提交到 `git` 裡面了？

小獅：那怎麼辦？

老獅：先把他刪除掉，我們後面讓他使用我們 `src/core/config.py` 裡面的 `Settings().DATABASE_URL`

```txt
# src/app/alembic.ini
# 刪除這一行
sqlalchemy.url = driver://user:pass@localhost/dbname
```
老獅：我們可以看到 `src/app/migrations/env.py` 這檔案裡面有不少程式，其中我們最感興趣的就是 `run_migrations_offline`, `run_async_migrations` 這邊我們想辦法讓他使用 `src/core/config.py` 裡面的 `Settings().DATABASE_URL`

```python
# src/app/migrations/env.py
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 這邊我們 import 自己的 config 進來
from core import config as core_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


# 我們建立了一個 function 讓我們有需要修改的程式都可以拿到一樣的 DATABASE_URL
def get_url() -> str:
    return core_config.Settings().DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # 把它改掉！
    # 原始程式：url = config.get_main_option("sqlalchemy.url")
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 這邊我們把原本 async_engine_from_config 的第一個參數抽出來
    configuration = config.get_section(config.config_ini_section)
    # 用我們的 get_url function 去指定 sqlalchemy.url
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

老獅：再來，我們需要讓他知道，要去哪看哪些 model 來參照，依照他上面的註解，我們知道要給 sqlalchemy 的 base.metadata，由於此 `class` 的階層比較靠近資料庫，也就是說， `models` 下面的 `class` 都是繼承他來使用，所以我們可以放心把他抽離出來，放到 `db/bases.py`

```python
# src/app/db/bases.py
import typing

from sqlalchemy import orm


@orm.as_declarative()
class Base:
    id: typing.Any
    __name__: str

    # Generate __tablename__ automatically
    @orm.declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
```

老獅：當然此時我們必須重構原本的 user model

```python
# src/app/models/auth.py
import sqlalchemy

from app.db import bases as model_bases


class User(model_bases.Base):
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, index=True)
    username = sqlalchemy.Column(sqlalchemy.String, index=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
```
老獅：最後我們重改 `env.py`，把 `Base` 給他

```python
# 新增這行
from app.db import bases as model_bases

# 拿掉這行
target_metadata = None

# 新增這行
target_metadata = model_bases.Base.metadata
```

## 製作 migration 檔案
老獅：我們來看看他能不能產生對應的檔案

```shell
cd src/app/ && python -m alembic revision --autogenerate -m "test"
/Users/super/project/fastit/src
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
  Generating /Users/super/project/fastit/src/app/migrations/versions/6daeb4107eb5_test.py ...  done
```
老獅：打開看看

```shell
cat /Users/super/project/fastit/src/app/migrations/versions/6daeb4107eb5_test.py
"""test

Revision ID: 6daeb4107eb5
Revises:
Create Date: 2023-09-10 20:22:14.343378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6daeb4107eb5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
```

小獅：看不出來有啥

老獅：是的，我們已經告訴他該注意哪個樹根發出來的樹葉，但是我們沒有把樹葉給他

小獅：人話？

老獅：我們和他說要去找 `app.db.bases.Base` 相關的 `class` 來產生資料表，但是我們並沒有在任何地方(執行 revision 指令時) `import` 他們，以下我們可以很簡單的去讓他知道

```python
# src/app/db/__init__.py
from app.models import auth
```

小獅：為啥寫這會動？

老獅：因為你在 `from app.db import bases` 時會自動執行該檔案，再來試試看

```shell
make migrations msg="add user table"
cd src/app/ && python -m alembic revision --autogenerate -m "add user table"
/Users/super/project/fastit/src
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
ERROR [alembic.util.messaging] Target database is not up to date.
  FAILED: Target database is not up to date.
make: *** [migrations] Error 255
```

小獅：啥意思？

老獅：因為剛剛那個檔案被他當作最後的版本，我們先把他刪掉重來
```shell
rm src/app/migrations/versions/*.py
```

```shell
cd src/app/ && python -m alembic revision --autogenerate -m "add user table"
/Users/super/project/fastit/src
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'user'
INFO  [alembic.autogenerate.compare] Detected added index 'ix_user_id' on '['id']'
INFO  [alembic.autogenerate.compare] Detected added index 'ix_user_username' on '['username']'
  Generating /Users/super/project/fastit/src/app/migrations/versions/ffcf55ddb7bd_add_user_table.py ...  done
```

老獅：看起來有點東西囉，你看有 `table` 有 `index` ，我們打開檔案來看

```shell
/Users/super/project/fastit/src/app/migrations/versions/b130fb2851db_add_user_table.py
"""add user table

Revision ID: b130fb2851db
Revises:
Create Date: 2023-09-09 16:11:29.085915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b130fb2851db'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###
```

小獅：哇嗚，真的產生出比較像 `SQL` 的指令咧！但是為啥我們要定義兩次？直接用 `models` 裡面的 `class` 不就可以產出對應的 SQL 了？

老獅：但是你新增修改欄位時你沒有辦法追蹤以及比較和現有資料庫的差異啊！

## 執行 migrate
老獅：好拉，有 migration 的檔案了，現在我們試著讓資料庫有這張表吧！

```shell
cd src/app/ && python -m alembic upgrade head
```

老獅：手動去資料庫看看
```shell
docker-compose exec postgres sh
(docker) / # psql -U postgres
postgres=# \c db
db=# \dt
 public | alembic_version | table | postgres
 public | user            | table | postgres

db=# \d "user"
                                  Table "public.user"
  Column  |       Type        | Collation | Nullable |             Default
----------+-------------------+-----------+----------+----------------------------------
 id       | integer           |           | not null | nextval('user_id_seq'::regclass)
 username | character varying |           |          |
 password | character varying |           | not null |
Indexes:
    "user_pkey" PRIMARY KEY, btree (id)
    "ix_user_id" btree (id)
    "ix_user_username" btree (username)
```
小獅：讚，該有的都有了，但是 `alembic_version` 是幹嘛用的

老獅：就是該套件紀錄你這個資料庫曾經 `migrate` 的紀錄，測試看看吧！

```shell
make test
pytest .
============================= test session starts ==============================
platform darwin -- Python 3.8.13, pytest-7.4.0, pluggy-1.2.0
rootdir: /Users/super/project/fastit
configfile: pyproject.toml
plugins: asyncio-0.21.1, anyio-3.7.1
asyncio: mode=auto
collected 3 items

src/tests/test_main.py .                                                 [ 33%]
src/tests/test_services/test_token.py .                                  [ 66%]
src/tests/test_units/test_users_crud.py .                                [100%]

============================== 3 passed in 0.84s ===============================
```

老獅：好拉，先提交吧！但測試先不要提交

小獅：為啥？

老獅：你先想想看吧！

```shell
git add requirements/
git add src/app/alembic.ini src/app/migrations/
git add src/app/db src/app/models/

git m "feat: add user table"
```

## Tree
```
.
├── Makefile
├── docker-compose.yml
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
    │   ├── alembic.ini  # 新增
    │   ├── api
    │   │   └── v1
    │   │       ├── endpoints
    │   │       │   └── auth
    │   │       │       └── users
    │   │       │           └── tokens.py
    │   │       └── routers.py
    │   ├── crud
    │   ├── db
    │   │   └── bases.py  # 新增
    │   ├── main.py
    │   ├── migrations    # 整個目錄都是新增，且都是自動產生的
    │   │   ├── README
    │   │   ├── env.py
    │   │   ├── script.py.mako
    │   │   └── versions
    │   │       └── b130fb2851db_add_user_table.py
    │   ├── models
    │   │   └── auth.py   # 新增
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
