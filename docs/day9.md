# 使用者驗證 - 由外而內測試
小獅：可是還沒有實作登入，怎麼測試？

老獅：就是要從沒有實作開始，放入你的構想，我們遇到錯誤才去補程式碼，這樣才不會多寫一些沒有用的東西出來

小獅：那我一樣去測試，建立 token 的情境，但是我沒有使用者，怎麼辦？

老獅：我們先寫死帳號密碼，再一步一步改成有資料庫的狀態

小獅：所以我先測試死的帳號密碼，然後要拿到可以登入的 `token` ，但是我們要怎麼測試他是可以用的 token ？

老獅：你可以寫一個解析 JWT token 的 API 提供客戶去了解他是否登入，以及他擁有的 `token` 裡面帶有哪些資訊 `GET /v1/auth/users/me`

小獅：理解，我們也可以反過來測試如果帶錯誤的 `token` 就拿不到東西

## 測試換取 Token
```python
# src/tests/test_services/test_token.py
import httpx
import pytest

from app import main


@pytest.mark.asyncio
async def test_create_jwt_token_by_username_and_passowrd():
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.post(
            "/v1/auth/users/tokens",
            json={"username": "test", "password": "testme"}
        )
        assert resp.status_code == 200
```

老獅：來跑看看
```shell
export PYTHONPATH=$PWD/src
pytest src
= test session starts =
platform darwin -- Python 3.8.13, pytest-7.4.0, pluggy-1.2.0
rootdir: /Users/super/project/fastit
plugins: asyncio-0.21.1, anyio-3.7.1
asyncio: mode=strict
collected 2 items

src/tests/test_main.py . [ 50%]
src/tests/test_services/test_token.py F [100%]

====== FAILURES ======
______________ test_create_jwt_token_by_username_and_passowrd ______________

    @pytest.mark.asyncio
    async def test_create_jwt_token_by_username_and_passowrd():
        async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
            resp = await client.post(
                "/v1/auth/users/tokens",
                json={"username": "test", "password": "testme"}
            )
>           assert resp.status_code == 200
E           assert 404 == 200
E            +  where 404 = <Response [404 Not Found]>.status_code

src/tests/test_services/test_token.py:14: AssertionError
== short test summary info ==
FAILED src/tests/test_services/test_token.py::test_create_jwt_token_by_username_and_passowrd - assert 404 == 200
== 1 failed, 1 passed in 0.39s ==

```

老獅：很明顯，我們沒有這個路由，來處理他吧！先寫空的 API

```python
# src/app/api/v1/auth/users/tokens.py
import fastapi

router = fastapi.APIRouter()


@router.post("")
def create_jtw_token():
    ...
```

老獅：利用 `APIRouter.include_router` 方法，把下面幾層的 APIRouter 一層一層的包進去，不過現在我們擁有的 API 還很少，先偷懶一下，後面再來做 `refactor`

```python
# src/app/api/v1/routers.py
import fastapi

from app.api.v1.endpoints.auth.users import tokens as token_endpoints

v1_router = fastapi.APIRouter()
v1_router.include_router(token_endpoints.router, prefix="/auth/users/tokens")
```

```python
# src/app/main.py
import fastapi

from app.api.v1 import routers as v1_routers
from app.models import health_check

app = fastapi.FastAPI()
app.include_router(v1_routers.v1_router, prefix="/v1")


# 省略...
```

老獅：跑測試吧

```shell
export PYTHONPATH=$PWD/src
pytest src
# 省略...
src/tests/test_main.py .                [ 50%]
src/tests/test_services/test_token.py . [100%]

=== 2 passed in 0.37s ===
```

小獅：太好了，他抓到這個 API 了，再來我就只要讓他可以吃到帳密然後可以回傳 `token` 就好了！

老獅：沒錯，我們來更新一下我們的測試
```python
# src/tests/test_services/test_token.py
import httpx
import pytest

from app import main


@pytest.mark.asyncio
async def test_create_jwt_token_by_username_and_passowrd():
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.post(
            "/v1/auth/users/tokens", json={"username": "test", "password": "testme"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
```

老獅：反覆為之直到完成此測試
```shell
export PYTHONPATH=$PWD/src
pytest src
# 省略...
=================================== FAILURES ===================================
________________ test_create_jwt_token_by_username_and_passowrd ________________

    @pytest.mark.asyncio
    async def test_create_jwt_token_by_username_and_passowrd():
        async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
            resp = await client.post(
                "/v1/auth/users/tokens", json={"username": "test", "password": "testme"}
            )
            assert resp.status_code == 200
            data = resp.json()
>           assert data["access_token"]
E           TypeError: 'NoneType' object is not subscriptable

src/tests/test_services/test_token.py:15: TypeError
=========================== short test summary info ============================
FAILED src/tests/test_services/test_token.py::test_create_jwt_token_by_username_and_passowrd - TypeError: 'NoneType' object is not subscriptable
========================= 1 failed, 1 passed in 0.40s ==========================
```
小獅：我好像只需要回傳對的東西就好，先來騙騙他

```python
import fastapi

router = fastapi.APIRouter()


@router.post("")
def create_jtw_token():
    return {"access_token": "access_token", "refresh_token": "refresh_token"}
```

```shell
export PYTHONPATH=$PWD/src
pytest src
# 省略...
src/tests/test_main.py .                [ 50%]
src/tests/test_services/test_token.py . [100%]

=== 2 passed in 0.37s ===
```

老獅：很棒，接下來我們來處理 `/v1/auth/users/me`

小獅：真的可以用騙的喔？

老獅：當然，這樣開發起來才不會多寫一堆沒用的東西，你就放心提交吧！

```shell
git add src/app/api/v1/endpoints/auth/users/tokens.py
git add src/app/api/v1/routers.py
git add src/app/main.py
git add src/tests/test_services/test_token.py
git commit -m "feat: add the endpoint to create JWT token"
```

## 本次目錄
```
.
├── docs
│   └── ...
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
    │   ├── api
    │   │   └── v1
    │   │       ├── endpoints
    │   │       │   └── auth
    │   │       │       └── users
    │   │       │           └── tokens.py   # 新增
    │   │       └── routers.py              # 新增
    │   ├── crud
    │   ├── db
    │   ├── main.py    # 更新
    │   ├── migrations
    │   ├── models
    │   │   └── health_check.py
    │   └── schemas
    ├── core
    │   └── config.py
    ├── scripts
    └── tests
        ├── test_main.py
        └── test_services
            └── test_token.py    # 新增
```
