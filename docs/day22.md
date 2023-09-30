# 重構
小獅：再來處理這兩段

```python
    obj_in_data = encoders.jsonable_encoder(user_info)
    user = auth_models.User(**obj_in_data)
    db.add(user)
    await db.commit()
    await db.flush()
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
老獅：這裡都和資料庫相關，主要是做資料庫的操作，我們可以把他們放到 `crud` 這個資料夾裡面

小獅：你會如何設計

```python
    obj_in_data = encoders.jsonable_encoder(user_info)
    user = auth_models.User(**obj_in_data)
    db.add(user)
    await db.commit()
```

老獅：這段很明顯就是就是在處理新增的部分，感覺重用性質很大，我們可以將其抽象成一個 `class` 主要做很基本的功能，像是這邊有的 `Create` 我們可以另外做 `Read`, `Update`, `Delete` 一些通用的功能，最後讓所有的 `model` 都可以使用類似的功能，這邊我們先不做過度抽象以及功能，後面有遇到其他 `model` 時，我們再來處理

```python
# src/app/crud/auth.py
from fastapi import encoders
from sqlalchemy.ext import asyncio as sqlalchemy_asyncio

from app.models import auth as auth_models


class CRUDUser:
    def __init__(self):
        self.model = auth_models.User

    async def create(
        self, db: sqlalchemy_asyncio.AsyncSession, obj_in: dict
    ):
        obj_in_data = encoders.jsonable_encoder(obj_in)
        user = self.model(**obj_in_data)
        db.add(user)
        await db.commit()
        return user
```

老獅：來改改有使用到新增使用者的程式們

```diff
diff --git a/src/tests/test_services/test_token.py b/src/tests/test_services/test_token.py
index d60b880..dde2011 100644
--- a/src/tests/test_services/test_token.py
+++ b/src/tests/test_services/test_token.py
@@ -2,13 +2,12 @@ import uuid
 
 import httpx
 import pytest
-from fastapi import encoders
 from passlib import context
 from passlib.hash import bcrypt
 from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
 
 from app import main
-from app.models import auth as auth_models
+from app.crud import auth as auth_crud
 
 
 @pytest.mark.asyncio
@@ -23,10 +22,7 @@ async def test_create_jwt_token_by_username_and_passowrd(
         "username": username,
         "password": password,
     }
-    obj_in_data = encoders.jsonable_encoder(user_info)
-    user = auth_models.User(**obj_in_data)
-    db.add(user)
-    await db.commit()
+    await auth_crud.user.create(db, user_info)
     await db.flush()
 
     resp = await client.post(
@@ -56,10 +52,7 @@ async def test_user_cannot_get_jwt_token_by_incorrect_passowrd(
         "username": username,
         "password": password,
     }
-    obj_in_data = encoders.jsonable_encoder(user_info)
-    user = auth_models.User(**obj_in_data)
-    db.add(user)
-    await db.commit()
+    await auth_crud.user.create(db, user_info)
     await db.flush()
     user_info["password"] = "invalidpassword"
 
@@ -103,10 +96,7 @@ async def test_create_token_by_username_and_passowrd_hash(
         "username": username,
         "password": password_hash,
     }
-    obj_in_data = encoders.jsonable_encoder(user_info)
-    user = auth_models.User(**obj_in_data)
-    db.add(user)
-    await db.commit()
+    await auth_crud.user.create(db, user_info)
     await db.flush()
 
     # 模擬前端
diff --git a/src/tests/test_units/test_users_crud.py b/src/tests/test_units/test_users_crud.py
index 4950530..243f2ec 100644
--- a/src/tests/test_units/test_users_crud.py
+++ b/src/tests/test_units/test_users_crud.py
@@ -1,9 +1,9 @@
 import pytest
 import sqlalchemy
-from fastapi import encoders
 from sqlalchemy import future as sqlalchemy_future
 from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
 
+from app.crud import auth as auth_crud
 from app.models import auth as auth_models
 
 
@@ -19,10 +19,8 @@ async def test_create_and_read_user(
         "password": password,
     }
     await db.execute(sqlalchemy.text("select 1"))
-    obj_in_data = encoders.jsonable_encoder(obj_in)
-    user = auth_models.User(**obj_in_data)
-    db.add(user)
-    await db.commit()
+    user = await auth_crud.user.create(db, obj_in)
+    await db.flush()
     user = (
         (
             await db.execute(
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

============================== 6 passed in 2.84s ===============================
```
老獅：很好，我們可以先提交這段程式碼

```shell
git add src/tests/test_services/test_token.py
git add src/tests/test_units/test_users_crud.py
git add src/app/crud/auth.py
git commit -m "refactor: move create user as a function to auth.user.create"
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

老獅：這段程式很明顯在撈資料，但是他除了有過濾欄位以外，還有給定特殊的轉化，我們會希望這種較為特規的需求會放在各自的 `class` 當中，這裡我們一樣簡單把他移過去 `crud.auth.CRUDUser` 就好

```python
# src/app/crud/auth.py
from sqlalchemy import func as sqlalchemy_func
from sqlalchemy import future as sqlalchemy_future


class CRUDUser:
    async def get_by_username(self, db: sqlalchemy_asyncio.AsyncSession, username: str):
        return (
            (
                await db.execute(
                    sqlalchemy_future.select(self.model).filter(
                        sqlalchemy_func.lower(self.model.username)
                        == sqlalchemy_func.lower(username)
                    )
                )
            )
            .scalars()
            .first()
        )
```

```diff
diff --git a/src/app/api/v1/endpoints/auth/users/hashes.py b/src/app/api/v1/endpoints/auth/users/hashes.py
index 5db9c02..b3a4e55 100644
--- a/src/app/api/v1/endpoints/auth/users/hashes.py
+++ b/src/app/api/v1/endpoints/auth/users/hashes.py
@@ -1,10 +1,8 @@
 import fastapi
-from sqlalchemy import func as sqlalchemy_func
-from sqlalchemy import future as sqlalchemy_future
 from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
 
 from app.api import dependencies
-from app.models import auth as auth_models
+from app.crud import auth as auth_crud
 from app.schemas import users as user_schemas
 
 router = fastapi.APIRouter()
@@ -15,18 +13,7 @@ async def get_hash_parameters(
     username: str,
     db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
 ):
-    user = (
-        (
-            await db.execute(
-                sqlalchemy_future.select(auth_models.User).filter(
-                    sqlalchemy_func.lower(auth_models.User.username)
-                    == sqlalchemy_func.lower(username)
-                )
-            )
-        )
-        .scalars()
-        .first()
-    )
+    user = await auth_crud.user.get_by_username(db, username)
     if not user:
         raise fastapi.HTTPException(
             fastapi.status.HTTP_404_NOT_FOUND, {"message": "Not Found"}
diff --git a/src/app/api/v1/endpoints/auth/users/tokens.py b/src/app/api/v1/endpoints/auth/users/tokens.py
index 34ff4f1..e24a1c9 100644
--- a/src/app/api/v1/endpoints/auth/users/tokens.py
+++ b/src/app/api/v1/endpoints/auth/users/tokens.py
@@ -5,12 +5,10 @@ import fastapi
 import jose
 from fastapi import security
 from jose import jwt
-from sqlalchemy import func as sqlalchemy_func
-from sqlalchemy import future as sqlalchemy_future
 from sqlalchemy.ext import asyncio as sqlalchemy_asyncio
 
 from app.api import dependencies
-from app.models import auth as auth_models
+from app.crud import auth as auth_crud
 from app.schemas import tokens as token_schemas
 from app.schemas import users as user_schemas
 from core import config
@@ -38,18 +36,7 @@ async def create_jtw_token(
     login: user_schemas.LoginInfo,
     db: sqlalchemy_asyncio.AsyncSession = fastapi.Depends(dependencies.get_db),
 ):
-    user = (
-        (
-            await db.execute(
-                sqlalchemy_future.select(auth_models.User).filter(
-                    sqlalchemy_func.lower(auth_models.User.username)
-                    == sqlalchemy_func.lower(login.username)
-                )
-            )
-        )
-        .scalars()
-        .first()
-    )
+    user = await auth_crud.user.get_by_username(db, login.username)
     if user and login.password == user.password:
         access_token = create_access_token(dict(sub=user.username))
         refresh_token = create_access_token(dict(sub=user.username))
diff --git a/src/tests/test_units/test_users_crud.py b/src/tests/test_units/test_users_crud.py
index 243f2ec..872eff6 100644
--- a/src/tests/test_units/test_users_crud.py
+++ b/src/tests/test_units/test_users_crud.py
@@ -21,17 +21,7 @@ async def test_create_and_read_user(
     await db.execute(sqlalchemy.text("select 1"))
     user = await auth_crud.user.create(db, obj_in)
     await db.flush()
-    user = (
-        (
-            await db.execute(
-                sqlalchemy_future.select(auth_models.User).where(
-                    auth_models.User.id == user.id
-                )
-            )
-        )
-        .scalars()
-        .first()
-    )
+    user = await auth_crud.user.get_by_username(db, username)
     assert user.username == "username"
     assert user.password == "password"
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

============================== 6 passed in 2.81s ===============================
```

小獅：舒爽多了！

```shell
git add src/app/api/v1/endpoints/auth/users/hashes.py
git add src/app/api/v1/endpoints/auth/users/tokens.py
git add src/app/crud/auth.py
git add src/tests/test_units/test_users_crud.py

git commit -m "refactor: add function to crud.auth.CRUDUser to get DB object by the username"
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
    │   │       │           ├── hashes.py    # 修改
    │   │       │           └── tokens.py    # 修改
    │   │       └── routers.py
    │   ├── crud
    │   │   └── auth.py    # 新增
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
        ├── conftest.py
        ├── test_main.py
        ├── test_services
        │   ├── test_hashes.py
        │   └── test_token.py      # 修改
        └── test_units
            └── test_users_crud.py # 修改
```
