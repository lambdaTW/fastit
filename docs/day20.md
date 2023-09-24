# 使用者驗證 - 權衡

小獅：誒都，不是啊，這樣我們是不是也是要在使用者給予密碼以前，要先給前端鹽巴以及 `HASH` 次數，不然前端怎麼做

老獅：對的，當使用者輸入帳號以後，我們應該先給前端演算法、鹽巴以及 `HASH` 次數，這樣前端才能夠將使用者輸入的密碼做 `HASH`

小獅：那如果他輸入錯的帳號怎麼辦

老獅：確實，如果他輸入錯誤的帳號，如果跟他說，就會變成駭客有機會利用暴力破解的方式，去猜使用者的帳號，這邊我們可以另外使用一些 `reCAPTCHA` 的機制減少此類攻擊，甚至在登入時，讓前端使用舊的演算法、鹽巴以及 `HASH` 次數做一次 `HASH`，另外在用相同的密碼明文，如果使用者密碼輸入正確，就順便更新資料庫的密碼 `HASH`

小獅：想起來好慢喔

老獅：確實，在考慮資安時，常常都是權衡說到底有沒有必要，其成本以及風險，如果我們是做金流或是比較跟錢有關係的系統，這些都會被拉放大鏡來看，但是如果我們只是個小系統，小新創，我們應該考量，怎樣設計會比較好改成更安全

小獅：看來兩階段登入是比較符合未來走向的，那我們就來實作，前端給予帳號，後端給予演算法、鹽巴以及 `HASH` 次數的 API 吧

老獅：是的，所以首先我們後端也要有 `bcrypt` 支援

```
# base.in
fastapi==0.101.1
uvicorn[standard]==0.23.2
python-jose[cryptography]==3.3.0
pydantic-settings==2.0.3
sqlalchemy[asyncio]==2.0.20
asyncpg==0.28.0
alembic==1.12.0
sqlalchemy-utils==0.41.1
passlib[bcrypt]==1.7.4
```

```shell
make pip
```

老獅：依照上述情境，我們可以先寫好流程，前端收到帳號，去問演算法、鹽巴以及 `HASH` 次數，最後以該演算法、鹽巴以及 `HASH` 次數來做 `HASH` 以後的密碼，以及剛剛輸入的帳號，去建立後面使用的 `token`，


```python
# src/tests/test_services/test_token.py
from passlib import context
from passlib.hash import bcrypt


@pytest.mark.asyncio
async def test_create_token_by_username_and_passowrd_hash(
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
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
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
```

```shell
make test
# 省略
>           assert resp.status_code == 200
E           assert 404 == 200
E            +  where 404 = <Response [404 Not Found]>.status_code

src/tests/test_services/test_token.py:115: AssertionError
```

小獅：這我知道我們補上路由

```python
# src/app/api/v1/endpoints/auth/users/hashes.py
import fastapi

router = fastapi.APIRouter()


@router.get("")
async def get_hash_parameters(
    username: str,
):
    ...
```

```python
# src/app/api/v1/routers.py
import fastapi

from app.api.v1.endpoints.auth.users import tokens as token_endpoints
from app.api.v1.endpoints.auth.users import hashes as hashes_endpoints


v1_router = fastapi.APIRouter()
v1_router.include_router(token_endpoints.router, prefix="/auth/users/tokens")
v1_router.include_router(hashes_endpoints.router, prefix="/auth/users/hashes")
```

```shell
make test
# 省略
>           alg, cost, salt = data["alg"], data["cost"], data["salt"]
E           TypeError: 'NoneType' object is not subscriptable

src/tests/test_services/test_token.py
```

老獅：這時我們想辦法從資料庫中拿到，該使用者密碼使用的 alg, cost, salt，並回傳回來

```python
# src/app/api/v1/endpoints/auth/users/hashes.py
import fastapi
from sqlalchemy import func as sqlalchemy_func
from sqlalchemy import future as sqlalchemy_future
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app.api import dependencies
from app.models import auth as auth_models

router = fastapi.APIRouter()


@router.get("")
async def get_hash_parameters(
    username: str,
    db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
):
    user = (
        (
            await db.execute(
                sqlalchemy_future.select(auth_models.User).filter(
                    sqlalchemy_func.lower(auth_models.User.username)
                    == sqlalchemy_func.lower(username)
                )
            )
        )
        .scalars()
        .first()
    )
    alg, cost, salt_and_hash = user.password.split("$")[1:]
    salt = salt_and_hash[:22]
    return {
        "alg": alg,
        "cost": cost,
        "salt": salt,
    }
```

```shell
make test
# 省略

src/tests/test_main.py .                                                 [ 20%]
src/tests/test_services/test_token.py ...                                [ 80%]
src/tests/test_units/test_users_crud.py .                                [100%]

============================== 5 passed in 2.60s ===============================
```

老獅：再來我們要來處理一下找不不到此人的情況

小獅：就直接回他 404 如何

老獅：恩恩恩，測試一下吧

```python
# src/tests/test_services/test_hashes.py
import uuid

import httpx
import pytest
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app import main


@pytest.mark.asyncio
async def test_create_token_by_username_and_passowrd_hash(
    migrate: None,
    db: sqlalchemy_asyncio.AsyncSession,
):
    username = str(uuid.uuid4())

    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.get(
            f"/v1/auth/users/hashes?username={username}",
        )
        assert resp.status_code == 404
```

```shell
make test
# 省略
>       alg, cost, salt_and_hash = user.password.split("$")[1:]
E       AttributeError: 'NoneType' object has no attribute 'password'

src/app/api/v1/endpoints/auth/users/hashes.py:34: AttributeError
```

小獅：在撈不到時直接回傳就好了

```python
# src/app/api/v1/endpoints/auth/users/hashes.py
# 省略
async def get_hash_parameters(
    username: str,
    db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
):
    # 省略
    if not user:
        raise fastapi.HTTPException(
            fastapi.status.HTTP_404_NOT_FOUND, {"message": "Not Found"}
        )
    alg, cost, salt_and_hash = user.password.split("$")[1:]
    # 省略
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
collected 6 items

src/tests/test_main.py .                                                 [ 16%]
src/tests/test_services/test_hashes.py .                                 [ 33%]
src/tests/test_services/test_token.py ...                                [ 83%]
src/tests/test_units/test_users_crud.py .                                [100%]

============================== 6 passed in 2.82s ===============================
```

小獅：耶！提交！

老獅：很好，但是你是不是忘了啥？

小獅：啥？

老獅：要讓前端做事前也要讓人家好做事情吧？

小獅：喔！ `Response model`

```python
# src/app/schemas/users.py

class HashInfo(pydantic.BaseModel):
    alg: str
    cost: int
    salt: str
```

```python
# src/app/api/v1/endpoints/auth/users/hashes.py
# 省略
from app.schemas import users as user_schemas

router = fastapi.APIRouter()


@router.get("", response_model=user_schemas.HashInfo)
async def get_hash_parameters(
    username: str,
    db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
):
    # 省略
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
collected 6 items

src/tests/test_main.py .                                                 [ 16%]
src/tests/test_services/test_hashes.py .                                 [ 33%]
src/tests/test_services/test_token.py ...                                [ 83%]
src/tests/test_units/test_users_crud.py .                                [100%]

============================== 6 passed in 2.82s ===============================
```

老獅：先提交吧

```shell
git add requirements/base.in
git add requirements/base.txt
git add src/app/api/v1/endpoints/auth/users/hashes.py
git add src/app/api/v1/routers.py
git add src/app/schemas/users.py
git add src/tests/test_services/test_token.py

git commit -m "feat: add hash info API for two step login"
```

# 本次目錄
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
    │   ├── alembic.ini
    │   ├── api
    │   │   ├── dependencies.py
    │   │   └── v1
    │   │       ├── endpoints
    │   │       │   ├── __init__.py
    │   │       │   └── auth
    │   │       │       └── users
    │   │       │           ├── hashes.py    # 新增
    │   │       │           └── tokens.py
    │   │       └── routers.py    # 修改
    │   ├── crud
    │   ├── db
    │   │   ├── __init__.py
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
    │       └── users.py    # 修改
    ├── core
    │   └── config.py
    └── tests
        ├── conftest.py
        ├── test_main.py
        ├── test_services
        │   ├── test_hashes.py   # 新增
        │   └── test_token.py    # 修改
        └── test_units
            └── test_users_crud.py
```
