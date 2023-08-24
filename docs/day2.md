# 專案目錄
小獅：專案目錄，是長怎樣的？

## 參考
老獅：專案目錄，我們參考了 FastAPI 作者的 [專案範本](https://github.com/tiangolo/full-stack-fastapi-postgresql) 並且簡化成只有開發 API 的版本，如果有興趣的人可以看看作者使用 `cookiecutter` 製作的其他專案結構，其中包括

- Full Stack FastAPI PostgreSQL
- Full Stack FastAPI Couchbase
- Full Stack FastAPI MongoDB
- Machine Learning models with spaCy and FastAPI

## 目錄本人
老獅：你可以看到以下空白的專案目錄以及說明，我們未來會慢慢填滿他
```txt
.
├── docs    # 我放至此文章的地方，您可以寫你的專案文件
│   ├── day1.md
│   └── day2.md
├── requirements        # 放各式套件組合
│   ├── base.in         # 必要套件
│   ├── base.txt        # 程式自動產生的必要套件以及他的依賴
│   ├── development.in  # 開發時需要的套件
│   └── development.txt # 程式自動產生的開發時需要的套件以及他的依賴
├── requirements.txt    # 必要安裝套件通常指向 `requirements/base.txt`
└── src
    ├── app
    │   ├── __pycache__
    │   ├── api    # 真的 API 程式碼放這邊
    │   │   └── v1
    │   │       └── endpoints
    │   │           └── __init__.py
    │   ├── crud          # 對資料庫進行操作的程式碼
    │   ├── db            # 資料庫核心程式碼
    │   ├── migrations    # 對資料庫進行資料表遷移的程式碼 (大部分由 alembic 自動產生)
    │   ├── models        # 資料表 <-- 對應 --> Python 程式
    │   └── schemas       # 和客戶端交換的資料 (byte)  <-- 對應 --> Python 程式
    ├── tests             # 測試程式碼
    ├── core              # 設定檔或是其他專案共用的程式碼放這邊
    └── scripts           # 其他腳本程式碼
```

## 如何開始
小獅：目錄建立好了，還有什麼步驟要做嗎？

### Git
老獅：我們使用 git 做版本控制，因此請先安裝 `git` 並且初始化此專案，並且先把 Python 用的 `.gitignore` 提交上去

```shell
# 初始化專案版控
git init

# 下載 Python 用 .gitignore
curl -o .gitignore https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore

# 提交 .gitignore
git add .gitignore
git commit -m "build: add .gitignore"
```
