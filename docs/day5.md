# 開發規範

小獅：接下來？

老獅：你是不是少做了什麼？你忘了公司的程式碼規範嗎？你這樣丟上去你覺得可以嗎？

小獅：對吼！那些規範總是令我害怕，是不是又要裝東西？

老獅：好的程式規範是讓大家都可以相對快速的完成工作，我們乖乖把他們弄好吧！

## 安裝開發套件
老獅： 先處理必要套件吧，我們要支援 `flake8`, `black`, `isort` 都把它寫進去 `development.in`

```txt
flake8==6.1.0
black==23.7.0
isort==5.12.0
```

老獅：讓 `pip-tools` 幫我們安裝吧

```shell
# 產生所有依賴
ls requirements/*.in | xargs -n1 pip-compile --resolver=backtracking --strip-extras
# 安裝所有套件以及其依賴
pip-sync `ls requirements/*.txt`
```

## 調整開發套件
小獅：可以讓他自動排版了吧？

老獅：你忘了設定，到時候他又把 `venv` 裡面的程式重新排版，今天就可以下班了，而且有些東西他們可是會打架的喔！先改改設定吧！免得一個排完另一個報錯

```txt
# setup.cfg
[flake8]
max-line-length = 88
exclude = venv/
ignore =
  W503,
  E203
```
```toml
# pyproject.toml
[tool.black]
line-length = 88
exclude = '''
/(
  | venv
)/
'''

[tool.isort]
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88
extend_skip = [
    "venv",
]
```

## 自動排版
小獅：那我就開始囉？

老獅：請

```shell
# 自動排版
python -m black .

# 自動整理 import 順序
python -m isort .

# 排版檢查
python -m black --check .

# import 順序檢查
python -m isort -c .

# python 基本寫作規則檢查
python -m flake8 .
```

小獅：這要先提交嗎？

老獅：是的，儘量不要和程式的 commit 混在一起

```shell
git add setup.cfg
git add pyproject.toml
git add requirements/

git commit -m "chore: add lint tools and lint config"
```


# 本次目錄
```
.
├── docs
│   ├── day1.md
│   ├── day2.md
│   ├── day3.md
│   ├── day4.md
│   └── day5.md
├── pyproject.toml    # 新增
├── requirements
│   ├── base.in
│   ├── base.txt
│   ├── development.in     # 新增
│   └── development.txt    # 新增
├── requirements.txt
├── setup.cfg    # 新增
└── src
    ├── app
    │   ├── __pycache__
    │   ├── api
    │   │   └── v1
    │   │       └── endpoints
    │   │           └── __init__.py
    │   ├── crud
    │   ├── db
    │   ├── main.py    # 新增
    │   ├── migrations
    │   ├── models
    │   └── schemas
    ├── tests
    ├── core
    └── scripts
```
