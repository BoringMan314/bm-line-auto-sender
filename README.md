# LINE 自動訊息發送機器人

## 簡介
這是一個使用 Python 開發的自動化工具，能透過 **LINE 桌面版** 自動發送訊息。  
支援功能：
- 依聊天室名稱定時自動發送
- 使用 JSON 設定聊天室、訊息與時間

## 安裝
1. 下載專案
   ```bash
   git clone https://github.com/BK1017/line-auto-sender.git
   cd line-message-bot
   ```
2. 安裝套件

   若沒有安裝Python，請到[這裡](https://www.python.org/downloads/)
   ```bash
   pip install -r requirements.txt
   ```
## 使用方式

1. 確認你的電腦已安裝 LINE 桌面版

2. 編輯 `messages.json`，指定聊天室、內容與排程。收件者可使用 `recipients` 指定名稱，或用 `recipient_count` 指定左側清單最上方幾個聊天室；兩者不可同時使用：
   ```json
   [
     {
       "recipients": ["王小明", "專案群組"],
       "message": "早安",
       "schedule": {
         "type": "daily",
         "times": ["09:00", "18:00"]
       }
     }
   ]
   ```

   依清單排序發送的範例：
   ```json
   {
     "recipient_count": 3,
     "message": "早安",
     "schedule": {"type": "daily", "times": ["09:00"]}
   }
   ```

   `schedule` 可使用以下四種模式：

   | 類型 | 設定範例 | 說明 |
   | --- | --- | --- |
   | 單次 | `{"type": "once", "datetime": "2026-09-15 09:00"}` | 只在指定日期與時間傳送一次。 |
   | 每日 | `{"type": "daily", "times": ["09:00", "18:00"]}` | 每天於一個或多個時間傳送。 |
   | 每週 | `{"type": "weekly", "weekday": "星期一", "times": ["09:00"]}` | 每週指定單一星期傳送；星期可填 `星期一` 至 `星期日`。 |
   | 每週多天 | `{"type": "weekly", "weekdays": ["星期一", "星期三"], "times": ["09:00"]}` | 每週多個指定星期傳送。 |
   | 單日多時段 | `{"type": "one_day", "date": "2026-09-15", "times": ["09:00", "13:00", "18:00"]}` | 僅在指定日期的多個時間傳送。 |

3. 執行程式
   ```bash
   python main.py
   ```

4. 若不確定聊天室名稱，可雙擊 `02.列出所有聊天室.bat`。它會建立 `聊天室名稱.txt`；將其中名稱複製到 `recipients` 即可。
## 注意事項

* 需要 Windows 環境（因為使用 pywinauto 操作桌面應用程式）

* LINE 必須保持登入狀態

* `recipients` 中的每個名稱，必須與 LINE 左側清單顯示的聊天室名稱完全相同。

* 程式需要持續執行，才能在指定時間發送訊息

