# 超級使用者 - 參數測試

```
2. 超級使用者可建立超級使用者
```

小獅：這容易，改個參數而已

老獅：別忘記要測試最後使用者在資料庫的權限是否真的是如同你輸入的一樣

```python
# src/tests/test_services/test_users.py
async def test_superuser_can_create_superuser(
    db: sqlalchemy_asyncio.AsyncSession,
    client: httpx.AsyncClient,
    superuser_client: httpx.AsyncClient,
):
    username = str(uuid.uuid4())
    password = str(uuid.uuid4())
    user_info = {
        "username": username,
        "password": password,
        "is_superuser": True,
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
```

老獅：有沒有發現他和上面那個 `test_superuser_can_create_user` 有 87% 相似

小獅：有喔，有什麼好方法讓他看起來比較不會那麼重複嗎？

老獅：`pytest` 提供了不少傳入測試參數的方法，我們可以簡單地給予 `@pytest.mark.parametrize` 這樣的 `decorator` 讓他自動產生不同參數，並且餵到該測試的參數中，他也會幫你跑成多個測試，讓你可以方便知道，哪個參數的測試壞了

```python
# src/tests/test_services/test_users.py

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
collected 8 items

src/tests/test_main.py .                                                 [ 12%]
src/tests/test_services/test_hashes.py .                                 [ 25%]
src/tests/test_services/test_token.py ...                                [ 62%]
src/tests/test_services/test_users.py ..                                 [ 87%]
src/tests/test_units/test_users_crud.py .                                [100%]

============================== 8 passed in 3.52s ===============================
```

小獅：好，剩下權限的部分

```
3. 一般使用者不能建立帳號密碼
```

```python
# src/tests/test_services/test_users.py
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
```

```shell
make test
# 省略
=========================== short test summary info ============================
FAILED src/tests/test_services/test_users.py::test_user_cannot_create_superuser - assert 201 == 403
========================= 1 failed, 8 passed in 3.90s ==========================
make: *** [test] Error 1
```

小獅：我們要想辦法從 DB 撈出使用者是不是 superuser

```diff
src/app/api/v1/endpoints/auth/users/users.py
@@ -1,17 +1,42 @@
 import fastapi
+import jose
+from fastapi import security
+from jose import jwt
 from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

 from app.api import dependencies
 from app.crud import auth as auth_crud
 from app.schemas import users as users_schemas
+from core import config

 router = fastapi.APIRouter()


 @router.post("", status_code=201)
 async def create_user(
+    token: str = fastapi.Depends(security.OAuth2PasswordBearer(tokenUrl="token")),
     user_info: users_schemas.UserInfo = fastapi.Body(),
     db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
 ):
+    credentials_exception = fastapi.HTTPException(
+        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
+        detail="Could not validate credentials",
+        headers={"WWW-Authenticate": "Bearer"},
+    )
+    try:
+        payload = jwt.decode(
+            token,
+            config.Settings().authjwt_secret_key,
+            algorithms=["HS256"],
+        )
+        username: str = payload.get("sub")
+        if username is None:
+            raise credentials_exception
+    except jose.JWTError:
+        raise credentials_exception
+    action_user = await auth_crud.user.get_by_username(db, username)
+
+    if not action_user.is_superuser:
+        raise fastapi.HTTPException(status_code=fastapi.status.HTTP_403_FORBIDDEN)
```

老獅：要不要匿名使用者也測一下

小獅：好主意，原本的 `client` 就是匿名使用者了對吧！

老獅：是的，因為我們沒有幫他放 `token` 在 `header`


```python
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
collected 10 items

src/tests/test_main.py .                                                 [ 10%]
src/tests/test_services/test_hashes.py .                                 [ 20%]
src/tests/test_services/test_token.py ...                                [ 50%]
src/tests/test_services/test_users.py ....                               [ 90%]
src/tests/test_units/test_users_crud.py .                                [100%]

============================== 10 passed in 3.81s ==============================
```

小獅：又一堆重複的程式碼，不會又要重構吧

老獅：是的，相信我們可以做得更好，但是那是之後的事情，測試寫好以後，我們就不怕改壞了，先提交吧

```shell
git add src/app/api/v1/endpoints/auth/users/users.py
git add src/tests/test_services/test_users.py
git commit -m "feat: block none superuser permission client to create a user" -m "test: user cannot create superuser" -m "test: anonymous cannot create superuser"
```

# 本次目錄
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
    │   └── config.py
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
