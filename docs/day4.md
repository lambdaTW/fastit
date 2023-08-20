# 第一隻程式
問：可以寫程式了嗎？

答：你知道要寫什麼嗎？

問：需求來就寫啊？

答：你有沒有想過要先寫一些簡單的東西確定程式會動？

問：要怎麼做？

答：你應該清楚 [HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview) 請求與回應以及 [API](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview#apis_based_on_http) 是什麼了吧？

問：我已經有這些先備知識了，也知道整個 API 的演化歷史，XML -> JSON -> 現代協定...，你問這個幹嘛？

答：有就太好了，我們就來寫一個確保服務有起來的程式，當作健康檢查用如何？


## 檢查點
答：我們使用根目錄 `/` 來當我們的檢查點，內容簡單說明這個 API Server 是用來做什麼的，以後我們也可以加入一些版本資訊，後面讓其他做監控的程式可以留下更多有用的 Log，以方便後續做除錯或是查找問題使用

```python
# src/app/main.py
import fastapi

app = fastapi.FastAPI()


@app.get("/")
def root():
    return {"api": "fastit"}
```

問：這太簡單了吧？我啊罵都看得懂，其中 `app` 應該就是程式主體，`app.get` 應該是用了註冊的方式把 `/` 這個路由註冊進去對吧？

答：沒錯，有了這行程式我們就可以簡單地把服務跑起來，確認看看他是否回應我們我們要的資料

```shell
# 先把程式路徑的 `src` 放到 PYTHONPATH 讓 python 可以正確 import 到該目錄下面的程式
export PYTHONPATH=$PWD/src

# 啟動服務，並且監控程式有改動時自動重啟服務
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 測試服務
curl http://localhost:8000
{"api":"fastit"}
```

問：太簡單了吧

答：那還不快提交程式碼

```shell
git add src/app/main.py
git commit -m "feat: add an API for health check"
```


# 本次目錄
```
.
├── docs
│   ├── day1.md
│   ├── day2.md
│   ├── day3.md
│   └── day4.md
├── requirements
│   ├── base.in
│   └── base.txt
├── requirements.txt
└── src
    └── app
        ├── __pycache__
        ├── api
        │   └── v1
        │       └── endpoints
        │           └── __init__.py
        ├── core
        ├── crud
        ├── db
        ├── main.py    # 新增
        ├── migrations
        ├── models
        ├── schemas
        ├── scripts
        └── tests
```
