# 超級使用者

小獅：很好，使用者可以登入了，我們系統要怎麼讓使用者擁有帳號

老獅：恩，我們可以提供幾個常見的內部系統初始方案給 PM，例如

1. PM 提供帳號密碼，我們使用 `script` 去增加與修改使用者
2. 提供 PM 一個超級使用者帳號，並且提供創建帳號以及修改密碼的介面，讓他可以創造修改使用者，不用通過我們

小獅：這種方式確實都滿合適的，但是如果我們這種小系統之後大起來是不是方案 2 比較直接？

老獅：你要知道兩個方案會花的時間不一樣，如果他要快，當然就是先選方案 1.，我們可以快速完成任務，就商業上而言，能在需要的時間內完成最大滿足是他們最先考慮的，我們工程師能做的是為其想好退路，以及提供未來可能會發生的事，提供他們參考風險與後續技術債的成本，最後還是會希望在其中間取到平衡

小獅：好，那我們來約個會議吧！

---

會議中

---

小獅：嘿嘿，他們選方案 2. 耶

老獅：恩，超級使用者你會怎麼設計？

小獅：這簡單，用一個 Flag 就可以解決了，反正他就最大，之後有需要再來用更複雜的權限系統，儘管導入更加複雜的權限系統，該 `Flag` 也不會太難整合到其他系統，只因他最大，寫一個例外即可

老獅：很好，那最一開始如何擁有初始的超級使用者來建立後續的超級使用者？

小獅：直接寫 DB 可以吧？

老獅：那當然是可以啊，啊你要記得捏

小獅：有辦法讓他自動化嗎？

老獅：你可以寫個 `script` 在系統部署時自動產生

小獅：那產生出來的帳號密碼不就寫在程式裡面了？

老獅：你可以用環境變數

小獅：喔，這樣甚至可以忘記密碼時改環境變數讓他幫我改成新密碼嗎？

老獅：你要也不是不行
