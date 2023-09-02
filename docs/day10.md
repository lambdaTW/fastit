# 使用者驗證 - 登入資訊

老獅：我們來加強我們的登入測試，拿完 `token` 以後把他拿去打 `/v1/auth/users/tokens/info` 期望他可以回應我們正確的資訊

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
        assert (access_token := data["access_token"])
        assert data["refresh_token"]
        resp = await client.get(
            "/v1/auth/users/tokens/info",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["username"] == "test"
```

```shell
export PYTHONPATH=$PWD/src
pytest src

...
>           assert resp.status_code == 200
E           assert 404 == 200
E            +  where 404 = <Response [404 Not Found]>.status_code

src/tests/test_services/test_token.py:21: AssertionError
=========================== short test summary info ============================
FAILED src/tests/test_services/test_token.py::test_create_jwt_token_by_username_and_passowrd - assert 404 == 200
========================= 1 failed, 1 passed in 0.39s ==========================
```

小獅：我會，加入新的函數去處理這個路徑，這簡單

```python
# src/app/api/v1/endpoints/auth/users/tokens.py

@router.get("/info")
def get_jtw_token_info():
    return {"username": "test"}
```

老獅：沒錯，我們再跑一次測試

```shell
export PYTHONPATH=$PWD/src
pytest src

============================= test session starts ==============================
platform darwin -- Python 3.8.13, pytest-7.4.0, pluggy-1.2.0
rootdir: /Users/super/project/fastit
plugins: asyncio-0.21.1, anyio-3.7.1
asyncio: mode=strict
collected 2 items

src/tests/test_main.py .                                                 [ 50%]
src/tests/test_services/test_token.py .                                  [100%]

============================== 2 passed in 0.37s ===============================
```

老獅：很棒，先提交吧

```shell
git add src/app/api/v1/endpoints/auth/users/tokens.py
git add src/tests/test_services/test_token.py

git commit -m "feat: get username from token info"
```

小獅：但是這樣測試很不完整吧？我們根本沒有驗證

老獅：是的，接下來我們就要把整個測試改進成為比較完整一點，例如我們可以測試不同帳號密碼登入以後拿到的帳密不一樣

小獅：只有兩個還是可以用騙的吧？

老獅：確實，所以這都是建立在你已經知道如何建立系統的情況下，我們知道為了符合更多種類的變異性，我們必須要把使用者資訊存起來，例如帳號密碼，最後我們就可以用存下來的帳號密碼來做驗證，分別給不同使用者發出不同的 token

小獅：終於要導入資料庫了，我們如何開始？

## 本次目錄
```
.
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
    │   │       │           └── tokens.py    # 更新
    │   │       └── routers.py
    │   ├── crud
    │   ├── db
    │   ├── main.py
    │   ├── migrations
    │   ├── models
    │   └── schemas
    │       └── health_check.py
    ├── core
    │   └── config.py
    ├── scripts
    └── tests
        ├── test_main.py
        └── test_services
            └── test_token.py    # 更新
```
