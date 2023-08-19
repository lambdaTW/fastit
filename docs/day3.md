# Python 套件管理
問：可以寫程式了嗎？

## 虛擬環境
答：裝好 `git` 以後，我們需要使用 Python 的虛擬環境來隔離專案使用的套件和系統使用的套件，防止專案套件和系統套件相互污染

```shell
# 建立虛擬環境
python -m venv venv

# 進入虛擬環境
source venv/bin/activate
```

## 安裝套件
答：我們使用 `pip-tools` 來做套件管理，將其設定好以後，最後我們就可以真的安裝 FastAPI 本人了

```shell
# 安裝 pip-tools
pip3 install -U pip && pip3 install -U pip-tools
```
答：更新以下檔案讓我們可以安裝套件 (第一行是註解，表示該檔案位置)
```txt
# requirements.txt
-r requirements/base.txt
```
```txt
# requirements/base.in
fastapi==0.101.1
uvicorn[standard]==0.23.2
```
答：最後我們讓 `pip-tools` 幫我們產生依賴套件，並且安裝所有套件以及其依賴

```shell
# 產生所有依賴
ls requirements/*.in | xargs -n1 pip-compile --resolver=backtracking --strip-extras
# 安裝所有套件以及其依賴
pip-sync `ls requirements/*.txt`

```
問：如何確定我裝好了
答：你可以列出你安裝好的套件，看有沒有和我差不多的輸出


```shell
# 列出安裝好的套件們
pip list
Package           Version
----------------- -------
annotated-types   0.5.0
anyio             3.7.1
build             0.10.0
click             8.1.7
exceptiongroup    1.1.3
fastapi           0.101.1
h11               0.14.0
httptools         0.6.0
idna              3.4
packaging         23.1
pip               23.2.1
pip-tools         7.3.0
pydantic          2.2.1
pydantic_core     2.6.1
pyproject_hooks   1.0.0
python-dotenv     1.0.0
PyYAML            6.0.1
setuptools        56.0.0
sniffio           1.3.0
starlette         0.27.0
tomli             2.0.1
typing_extensions 4.7.1
uvicorn           0.23.2
uvloop            0.17.0
watchfiles        0.19.0
websockets        11.0.3
wheel             0.41.1
```

## 開始寫程式
問：我安裝都沒有問題了，可以開始寫程式了嗎？
答：明天再說拉，老闆給那麼少錢，先摸魚好嗎？先把今天的進度提交到 git 吧

```
git add src requirements requirements.txt
git commit -m "build: python packages" -m "build: basic folder structure"
```
