# 工欲善其事

老獅：你在提交程式碼以前都有記得做 `make lint-fix` 吧？

小獅：當然，但是在很多時候 `flake8` 會跑不過，還是要手動修改，尤其你那些產生出來的，我也是很辛苦吼！

```shell
python -m flake8 src
./app/migrations/versions/b130fb2851db_add_user_table.py:4:9: W291 trailing whitespace
```

老獅：真是辛苦你了吼！我們是可以放掉那些自動產生的程式碼拉，像是 `black` 和 `isort` 我們已經有略過 `venv` 了，但是 `flake8` 目前還沒有支援 `pyproject.toml` 要另外增加設定檔案: `setup.cfg`

小獅：不能都用 `pyproject.toml` 嗎？

老獅：也可以，但是我們就要換工具了

小獅：可以嗎？公司不是說。。。

老獅：現在有一個新工具: `ruff`

老獅：它和 `flake8` 提供差不多的功能，但是執行速度更快，也支援 `pyproject.toml` 我用起來是還算正常，我們可以把差異與優劣勢提供除來，先問看看樓上的，如果他們同意就可以導入了

~ A few monents later

老獅：由於是新專案，上面沒啥意見，我們就改吧

## 略過自動產生的程式碼檢查

## 安裝 ruff
```txt
# requirements/development.in
# lint and format
ruff==0.0.287
black==23.7.0
isort==5.12.0

# for tests
pytest-asyncio==0.21.1
pytest==7.4.0
httpx==0.24.1
```

```shell
make pip
```

老獅：我們幫他加上設定，讓他知道要注意哪些東西要警告
```toml
# pyproject.toml
[tool.ruff]
select = ["E", "F", "W"]
fixable = ["ALL"]
line-length = 88
# Assume Python 3.8
target-version = "py38"
```
## 更新 ruff 設定
老獅：好，現在我們就來試跑一下

```shell
python -m ruff src
src/app/migrations/versions/b130fb2851db_add_user_table.py:4:9: W291 [*] Trailing whitespace
```
老獅：很好，我們現在讓他略過 `migrations` 的檔案

```toml
[tool.ruff]
select = ["E", "F", "W"]
fixable = ["ALL"]
exclude = [
    ".git",
    "venv",
    "migrations",
]
line-length = 88
# Assume Python 3.8
target-version = "py38"
```

```shell
python -m ruff .
```

老獅：完美迴避

# 更新 Makefile

## 更新 `lint`
老獅：改了工具以後我們的 `make lint` 也要改成用 `ruff`

```
# Makefile
lint:  ## Run linting
	python -m black --check .
	python -m isort -c .
	python -m ruff .
.PHONY: lint
```

```shell
make lint
```

## 新增 migrations 與 migrate 指令
老獅：都改了，我們順便新增一下 `migrations` 與 `migrate` 指令

小獅：需要這酷東西，不然 `cd` 來 `cd` 去，我都不知道我在哪裡惹

```
# Makefile
migrate:  ## Migrate DB to head version
	cd src/app/ && python -m alembic upgrade head
.PHONY: migrate

migrations:  ## Make alembic migrations, ex: make migrations msg="create auth tables"
	cd src/app/ && python -m alembic revision --autogenerate -m "$(msg)"
.PHONY: migrations
```

老獅：由於現在沒有啥新的更新，你可以刪除資料庫以後，玩看看 `make migrate`，`make migrations msg="some message"` 就下次再來體驗吧

```shell
git add Makefile
git add pyproject.toml
git add requirements/development.in
git add requirements/development.txt
git commit -m "chore: update development tools"
```

## 本次目錄
```
.
├── Makefile               # 更新
├── docker-compose.yml
├── pyproject.toml         # 更新
├── requirements
│   ├── base.in
│   ├── base.txt
│   ├── development.in     # 更新
│   └── development.txt    # 更新
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
    │   │   ├── env.py
    │   │   ├── script.py.mako
    │   │   └── versions
    │   │       └── b130fb2851db_add_user_table.py
    │   ├── models
    │   │   └── auth.py
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
            └── test_users_crud.py
```
