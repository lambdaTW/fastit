# 插曲 - 重構
## 登出？
小獅：耶，可以登入了，來處理登出！

老獅：目前看需求登出好像沒有很要緊，要不要叫前端把 token 清掉就好了？

小獅：可以這樣偷懶喔？

老獅：不然你自己加班啊！

小獅：先不要，就這樣吧。

老獅：我們可以在會議中，給予安全性的警示，除非他們有要求，否則 PM 沒有要求的功能就不要自討苦吃，能簡單做就簡單做，因為他也不一定知道自己要什麼，先能使用，再讓他們來煩惱其他更細節的東西吧。

小獅：在空擋時是不是該來做點什麼

老獅：你覺得之前寫的程式如何？

小獅：我寫的當然完美無瑕，連 `lint` 都跑過了

## 重複者重構
老獅：你不覺得下面這些程式碼出現太多次嗎？
```python
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.post(
```
```python
    obj_in_data = encoders.jsonable_encoder(user_info)
    user = auth_models.User(**obj_in_data)
    db.add(user)
    await db.commit()
```

```python
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
```
小獅：好像是耶，`httpx.AsyncClient` 應該是可以用 pytest 的 `fixture` 處理掉對吧？其他兩個我是沒什麼想法

老獅：沒關係，那我們就先來處理他

```python
# src/tests/conftest.py
import httpx

from app import main

@pytest.fixture
async def client() -> typing.AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        yield client
```
小獅：好，再來就是一個一個改成使用它

```diff
diff --git a/src/tests/conftest.py b/src/tests/conftest.py
index 4e05b0b..909cb31 100644
--- a/src/tests/conftest.py
+++ b/src/tests/conftest.py
@@ -2,14 +2,22 @@ import pathlib
 import typing
 from unittest import mock
 
+import httpx
 import pytest
 from sqlalchemy import orm
 from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
 from sqlalchemy_utils import functions
 
+from app import main
 from core import config
 
 
+@pytest.fixture
+async def client() -> typing.AsyncIterator[httpx.AsyncClient]:
+    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
+        yield client
+
+
 @pytest.fixture
 def settings() -> typing.Iterator[config.Settings]:
     settings = config.Settings()
diff --git a/src/tests/test_main.py b/src/tests/test_main.py
index cc9f777..93ff938 100644
--- a/src/tests/test_main.py
+++ b/src/tests/test_main.py
@@ -1,12 +1,9 @@
 import httpx
 import pytest
 
-from app import main
-
 
 @pytest.mark.asyncio
-async def test_health_endpoint():
-    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
-        resp = await client.get("/")
-        assert resp.status_code == 200
-        assert resp.json() == {"api": "fastit", "version": None}
+async def test_health_endpoint(client: httpx.AsyncClient):
+    resp = await client.get("/")
+    assert resp.status_code == 200
+    assert resp.json() == {"api": "fastit", "version": None}
diff --git a/src/tests/test_services/test_hashes.py b/src/tests/test_services/test_hashes.py
index bb464c8..be59723 100644
--- a/src/tests/test_services/test_hashes.py
+++ b/src/tests/test_services/test_hashes.py
@@ -4,20 +4,18 @@ import httpx
 import pytest
 from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
 
-from app import main
-
 
 @pytest.mark.asyncio
 async def test_create_token_by_username_and_passowrd_hash(
+    client: httpx.AsyncClient,
     migrate: None,
     db: sqlalchemy_asyncio.AsyncSession,
 ):
     username = str(uuid.uuid4())
 
     # 模擬前端
-    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
-        # 先獲取 hash 資訊
-        resp = await client.get(
-            f"/v1/auth/users/hashes?username={username}",
-        )
-        assert resp.status_code == 404
+    # 先獲取 hash 資訊
+    resp = await client.get(
+        f"/v1/auth/users/hashes?username={username}",
+    )
+    assert resp.status_code == 404
diff --git a/src/tests/test_services/test_token.py b/src/tests/test_services/test_token.py
index d3f737a..d60b880 100644
--- a/src/tests/test_services/test_token.py
+++ b/src/tests/test_services/test_token.py
@@ -13,6 +13,7 @@ from app.models import auth as auth_models
 
 @pytest.mark.asyncio
 async def test_create_jwt_token_by_username_and_passowrd(
+    client: httpx.AsyncClient,
     migrate: None,
     db: sqlalchemy_asyncio.AsyncSession,
 ):
@@ -28,21 +29,20 @@ async def test_create_jwt_token_by_username_and_passowrd(
     await db.commit()
     await db.flush()
 
-    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
-        resp = await client.post(
-            "/v1/auth/users/tokens",
-            json=user_info,
-        )
-        assert resp.status_code == 200
-        data = resp.json()
-        assert (access_token := data["access_token"])
-        assert data["refresh_token"]
-        resp = await client.get(
-            "/v1/auth/users/tokens/info",
-            headers={"Authorization": f"Bearer {access_token}"},
-        )
-        assert resp.status_code == 200
-        assert resp.json()["username"] == username
+    resp = await client.post(
+        "/v1/auth/users/tokens",
+        json=user_info,
+    )
+    assert resp.status_code == 200
+    data = resp.json()
+    assert (access_token := data["access_token"])
+    assert data["refresh_token"]
+    resp = await client.get(
+        "/v1/auth/users/tokens/info",
+        headers={"Authorization": f"Bearer {access_token}"},
+    )
+    assert resp.status_code == 200
+    assert resp.json()["username"] == username
 
 
 @pytest.mark.asyncio
@@ -73,6 +73,7 @@ async def test_user_cannot_get_jwt_token_by_incorrect_passowrd(
 
 @pytest.mark.asyncio
 async def test_create_token_by_username_and_passowrd_hash(
+    client: httpx.AsyncClient,
     migrate: None,
     db: sqlalchemy_asyncio.AsyncSession,
 ):
@@ -109,26 +110,25 @@ async def test_create_token_by_username_and_passowrd_hash(
     await db.flush()
 
     # 模擬前端
-    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
-        # 先獲取 hash 資訊
-        resp = await client.get(
-            f"/v1/auth/users/hashes?username={username}",
-        )
-        assert resp.status_code == 200
-        data = resp.json()
-        alg, cost, salt = data["alg"], data["cost"], data["salt"]
-        # 利用回傳回來的 hash 資訊做密碼 hash
-        password_hash = bcrypt.using(
-            ident=alg,
-            rounds=cost,
-            salt=salt,
-        ).hash(password)
-        # 真正做登入
-        resp = await client.post(
-            "/v1/auth/users/tokens",
-            json={
-                "username": username,
-                "password": password_hash,
-            },
-        )
-        assert resp.status_code == 200
+    # 先獲取 hash 資訊
+    resp = await client.get(
+        f"/v1/auth/users/hashes?username={username}",
+    )
+    assert resp.status_code == 200
+    data = resp.json()
+    alg, cost, salt = data["alg"], data["cost"], data["salt"]
+    # 利用回傳回來的 hash 資訊做密碼 hash
+    password_hash = bcrypt.using(
+        ident=alg,
+        rounds=cost,
+        salt=salt,
+    ).hash(password)
+    # 真正做登入
+    resp = await client.post(
+        "/v1/auth/users/tokens",
+        json={
+            "username": username,
+            "password": password_hash,
+        },
+    )
+    assert resp.status_code == 200
```

```
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

============================== 6 passed in 2.80s ===============================
```
老獅：很好，先提交吧

```shell
git add src/tests
git commit -m "refactor: tests with the client fixture"
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
    │   │       │           └── tokens.py
    │   │       └── routers.py
    │   ├── crud
    │   │   ├── __init__.py
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
        ├── conftest.py           # 新增 fixture
        ├── test_main.py          # 修改
        ├── test_services
        │   ├── test_hashes.py    # 修改
        │   └── test_token.py     # 修改
        └── test_units
            └── test_users_crud.py
```
