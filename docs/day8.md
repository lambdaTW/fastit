# 使用者驗證 - 測試先行
小獅：可以實作登入了吧？

老獅：你 API 路徑要放哪？

小獅：`/login` 啊，全世界都是這樣吧

老獅：你想像中，使用者要帶什麼進來，你會回什麼回去？

小獅：
```txt
Request:
POST /login HTTP/1.1
...
{"username": "...", "password": "..."}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.....",
  "refresh_token": ...
}
```

老獅：你不覺得，其實你是在建立 token 嗎？

小獅：好像是耶！那用 RESTful 來看，應該要放 `/v1/auth/users/tokens`

```txt
Request:
POST /v1/auth/users/tokens HTTP/1.1
...
{"username": "...", "password": "..."}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.....",
  "refresh_token": ...
}
```

老獅：不錯，那就動手寫測試吧！

小獅：測試？

老獅：先拿我們的 `/` ，練練手吧
```txt
# requirements/development.in
# lint and format
flake8==6.1.0
black==23.7.0
isort==5.12.0

# for tests
pytest-asyncio==0.21.1
pytest==7.4.0
httpx==0.24.1
```

```shell
# 產生所有依賴
ls requirements/*.in | xargs -n1 pip-compile --resolver=backtracking --strip-extras
# 安裝所有套件以及其依賴
pip-sync `ls requirements/*.txt`
```

```python
# src/tests/test_main.py
import httpx
import pytest

from app import main


@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(app=main.app, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json() == {"api": "fastit", "version": None}
```

老獅：好拉，跑看看吧
```shell
export PYTHONPATH=$PWD/src
pytest src

== test session starts ==
platform darwin -- Python 3.8.13, pytest-7.4.0, pluggy-1.2.0
rootdir: /Users/super/project/fastit
plugins: asyncio-0.21.1, anyio-3.7.1
asyncio: mode=strict
collecting ...
collected 1 item

src/tests/test_main.py  [100%]

== 1 passed in 0.36s ==
```

老獅：看起來很完美

小獅：原來測試就是模擬瀏覽器的動作啊？

老獅：可以這樣想，如果你可以把前端會走過的路徑以及邏輯都跑過，這樣對於和前端的溝通也會有所幫助，好拉，先提交吧！

```shell
git add requirements
git add src/tests/test_main.py
git commit -m "test: the health endpoint"
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
│   ├── development.in     # 更改
│   └── development.txt    # pip-tools 指令更改
├── requirements.txt
├── setup.cfg
└── src
    ├── app
    │   ├── api
    │   │   └── v1
    │   │       └── endpoints
    │   │           └── __init__.py
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
        └── test_main.py    # 新增
```
