# 使用者驗證 - 初探

小獅：PM 說只要先讓使用者可以簡單的登入登出就好，我想我需要 `/login` 和 `/logout` 之類的 endpoints

老獅：你打算用什麼方式存使用者登入的資訊？

小獅：還想偷考啊！這年代簡單做當然是用 JWT 啊，帳密就簡單存在 PostgreSQL 就好了吧？我知道密碼要存加密的拉！雖然科技巨頭都存明文，嘻嘻

老獅：沒錯，想成為科技巨頭就是要存明文！才怪！

## 安裝套件
老獅：我剛好知道有一個套件可以裝，大部分 JWT 功能都有，有需要擴充的之後再處理吧！

```txt
requirements/base.in
fastapi==0.101.1
uvicorn[standard]==0.23.2
python-jose[cryptography]==3.3.0
```

```shell
# 產生所有依賴
ls requirements/*.in | xargs -n1 pip-compile --resolver=backtracking --strip-extras
# 安裝所有套件以及其依賴
pip-sync `ls requirements/*.txt`
```

## Pydantic
小獅：裝好了，然後呢？金鑰要存哪？

老獅：JWT 加密用的金鑰我們先存環境變數吧，Pydantic 的 `Settings` 可以幫助我們

```txt
requirements/base.in
fastapi==0.101.1
uvicorn[standard]==0.23.2
python-jose[cryptography]==3.3.0
pydantic-settings==2.0.3
```

```shell
# 產生所有依賴
ls requirements/*.in | xargs -n1 pip-compile --resolver=backtracking --strip-extras
# 安裝所有套件以及其依賴
pip-sync `ls requirements/*.txt`
```

老獅：只要設定好他就可以吃 `.env` 這檔案的環境變數了，當然，上伺服器以後你也可以直接喂環境變數到系統，只要在服務起起來以前給予就可以了
```python
# src/core/config.py
import pathlib

import pydantic_settings

PROJECT_PATH = pathlib.Path(__file__).parent.parent
print(PROJECT_PATH)


class Settings(pydantic_settings.BaseSettings):
    authjwt_secret_key: str = "secret"
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=PROJECT_PATH / ".env",
    )
```
老獅：設定一下 `.env`，我比較偷懶，都會把他提到 `src/.env` 如果你要直接吃 `src/core/.env` 也可以把 `PROJECT_PATH / ".env"` 改回 `.env` 就可以了

```shell
# src/.env
authjwt_secret_key=thisismynewsecret
```
老獅：先用 Python 測試一下有沒有吃到這個設定，可以動就先 commit 吧

```shell
PYTHONPATH=$PWD/src python
Python 3.8.13 (default, Feb  2 2023, 16:22:17)
[Clang 14.0.0 (clang-1400.0.29.202)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from core import config
>>> config.Settings()
Settings(authjwt_secret_key='thisismynewsecret')
>>> assert config.Settings().authjwt_secret_key == 'thisismynewsecret'
```

```shell
git add requirements
git commit -m "build: add jwt and config packages"

git add src/core
git commit -m m "feat: add jwt secret config"
```

小獅：啊你 `.env` 不留一份進去 `git` 嗎？
老獅：預設會被我們之前設定的 `.gitignore` 擋掉，你應該是加不進去的，以防你把真的機敏資料放進去 `git`，你如果怕設定被忘記，可以寫一份在 `README.md` 或是另外寫一份 `.env.example`，不過你就看看就好

```shell
echo "authjwt_secret_key=abcd" > .env.example
git add .env.example
git commit -m "..."
```

## 本次目錄
```
.
├── docs
│   └── ...
├── pyproject.toml
├── requirements
│   ├── base.in     # 更改
│   ├── base.txt    # pip-tools 指令更改
│   ├── development.in
│   └── development.txt
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
    │   └── config.py    # 新增
    ├── scripts
    └── tests
```
