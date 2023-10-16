# 使用者驗證 - 加密

小獅：真的要存明文密碼喔？

老獅：當然沒有，你知道現在加密密碼用什麼演算法比較好嗎？

小獅：不就用 `HASH` 把密碼原文變成難以反查的字串嗎？

老獅：由於現在電腦運算速度越來越快，為了避免單一次的 `HASH` 如果該算法已經公開了，駭客可以先暴力產生密碼原文，利用大量電腦去算出原文對應的 `HASH` ，之後如果有偷到資料庫的密碼，就可以用預先算好的彩虹表，來做反查，駭客就可以用已經得到的資料庫密碼去駭別的系統

老獅：我們可以自幹一個彩虹表，以下用英文大小寫的字元們做組合，產生兩位元的密碼表，並且使用 `sha256` 作為 `HASH` 演算法

```python
import string
import hashlib
import itertools


with open("/tmp/rainbow_table.csv", "w") as f:
    for password in list(''.join(pair) for pair in itertools.product(string.ascii_letters, repeat=2)):
        f.write(f"{password},{hashlib.sha256(password.encode('ascii')).hexdigest()}\n")
```

老獅：跑完以上 `Python` 程式以後，打開 `/tmp/rainbow_table.csv`，就可以看到被該原文被 `HASH` 後的樣子，如果我們今天在某個資料庫，拿到使用 `sha256` 作為 `HASH` 演算法的密碼欄位，我們就可以用文字搜尋的方式，反查到該密碼原文

```shell
head /tmp/rainbow_table.csv
aa,961b6dd3ede3cb8ecbaacbd68de040cd78eb2ed5889130cceb4c49268ea4d506
ab,fb8e20fc2e4c3f248c60c39bd652f3c1347298bb977b8b4d5903b85055620603
ac,f45de51cdef30991551e41e882dd7b5404799648a0a00753f44fc966e6153fc1
ad,70ba33708cbfb103f1a8e34afef333ba7dc021022b2d9aaa583aabb8058d8d67
ae,f9a00f43e97e3966bb846e76b6795e11512c3bbfa787e6b70e0310c7b9346b98
af,503126878d17fcd6bde7df320ff6eb7c278a1c42f30014a03b17f3dd0c023c1d
ag,9aaf680776b98fd17fe63376120525cbcdffc01bc66f71df96b6e90b87f39b86
ah,70a0d5198ebb88f97a2cc83a236a8afcc28c7d9e6abf40c173dd54c9f45ad7f6
ai,32e83e92d45d71f69dcf9d214688f0375542108631b45d344e5df2eb91c11566
aj,7d29d73105d636d04ca9fffcf979986d373ac874140bcb76ba86bc6975eae6a8
```

小獅：也太危險，那怎麼辦？

老獅：為此我們可以為不同的密碼，加入鹽巴，也就是另外的字串去做 `HASH`

```python
import secrets
import hashlib


def make_password_hash(password):
    salt = secrets.token_urlsafe()
    password += salt
    # 把密碼和鹽巴一起做 hash, 回傳 `HASH:鹽巴`，存在資料庫
    return hashlib.sha256(password.encode("ascii")).hexdigest() + f":{salt}"


password_in_db = make_password_hash("hello")
# 比對密碼時，從資料庫拿出來，把 HASH 後的值與鹽巴分開
password_hash, salt = password_in_db.split(":")

# 假設這是使用者輸入的密碼
user_input_password = "hello"
# 把使用者輸入的密碼和鹽巴做 `HASH`
user_input_password += salt
# 將使用者輸入的密碼和鹽巴做成 `HASH` 的值與資料庫內的 `HASH` 比對
if hashlib.sha256(user_input_password.encode("ascii")).hexdigest() == password_hash:
    print("Login")
else:
    print("Incorrect password")
```

小獅：所以只要做加鹽就好了，這容易

老獅：雖然他沒辦法預先產生好彩虹表，但是這樣還是有可能被暴力破解，假設說他拿到你的密碼那個欄位，他就可以用多台機器去產生明文，然後用一樣的鹽巴去做破解

小獅：所以要自幹演算法嗎？

老獅：你是密碼學家嗎？

小獅：不是

老獅：人家公開的演算法都是經過驗證的，你自己寫的搞不好有更容易被繞過的問題，除非你是專家，不然永遠不要想自幹，越公開的算法，越多人使用，表示越多人幫這個算法做驗證，很多資安學家每天想方設法要破解那些公開的算法，要記得，越多人驗證的東西相對安全，閉門造車只是鴕鳥心態

小獅：那我們該怎麼辦？

老獅：現在會使用多次 (2 ~ n 次) `HASH` 來將密碼原文做 `HASH` 讓攻擊者對反查原文的成本增加，如果重複 `HASH` 次數增加，每筆 `原文 -> HASH` 的計算時間會增加，想要暴力破解就會相對困難

小獅：有現成的可以用嗎？

老獅：有的 [bcrypt](https://en.wikipedia.org/wiki/Bcrypt) 提供該演算法，他大改長這樣

```
$2a$12$R9h/cIPz0gi.URNNX3kh2OPST9/PgBkqquzi.Ss7KIUgO2t0jWMUW
\__/\/ \____________________/\_____________________________/
Alg Cost      Salt                        Hash
```
老獅：Alg 演算法有很多選項

- $1$: MD5
- $2$: Blowfish，有很多版本，範例是 2a
  - 2a
  - 2x
  - 2y
  - 2b
- $sha1$: SHA-1
- $5$: SHA-256
- $6$: SHA-512

老獅：其中 `Cost` 是我們比較關心的，就是會重複 `HASH` 幾次拉

小獅：這樣每次登入我們電腦也會算比較久吧？

老獅：沒錯，看你要安全還是要速度囉

小獅：不能全都要嗎？我們是大人了對吧？

老獅：毛還沒長齊還自稱大人，那你先回答我做 `HASH` 這件事情要放前端還是後端？

小獅：這東西還有在放前端的喔？

老獅：如果說駭客進入到你的系統，有辦法在你做 `HASH` 以前拿到使用者輸入的密碼原文。。。

小獅：喔～所以說如果在前端做 `HASH` 的話，除非駭客是駭進去使用者的裝置，不然沒辦法拿到原文，至少不是每個近來我們網站的使用者都有可能被得知密碼原文

老獅：沒錯，叫 PM 開票給前端吧！

小獅：讚拉
