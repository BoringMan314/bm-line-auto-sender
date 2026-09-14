from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import time, json, schedule, datetime, os
from functools import partial

# === 可調整變數 ===
# LINE 路徑：優先使用 Windows 的 Local AppData；部分安裝環境則使用 AppData。
LINE_PATHS = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "LINE", "bin", "LineLauncher.exe"),
    os.path.join(os.environ.get("APPDATA", ""), "LINE", "bin", "LineLauncher.exe"),
]
# 訊息檔案路徑
JSON_PATH = "messages.json"

# === 啟動或連線 LINE ===
def check_line_running(retry=3, delay=5):
    for attempt in range(retry):
        try:
            app = Application(backend="uia").connect(title_re="LINE")
            return app
        except Exception as e:
            if attempt == 0:
                try:
                    line_path = next((path for path in LINE_PATHS if os.path.isfile(path)), None)
                    if not line_path:
                        raise FileNotFoundError("找不到 LINE 執行檔，請確認 LINE 桌面版已安裝。")
                    app = Application(backend="uia").start(line_path)
                    time.sleep(delay)
                except Exception as start_err:
                    print(f"啟動 LINE 失敗: {start_err}")
            time.sleep(delay)
    print("連線或啟動 LINE 失敗，請確認 LINE 是否安裝或路徑正確。")
    return None
app = check_line_running()
if app is None:
    raise SystemExit(1)

win = app.window(title_re="LINE")
win.set_focus()

# === 發送訊息函式 ===
def find_chat(recipient):
    """從 LINE 左側聊天清單尋找名稱完全相同的聊天室。"""
    lists = win.descendants(control_type="List")
    if not lists:
        raise RuntimeError("找不到 LINE 聊天清單。")

    chat_list = max(lists, key=lambda item: len(item.children()))
    for chat_item in chat_list.children():
        names = [chat_item.window_text()]
        names.extend(element.window_text() for element in chat_item.descendants(control_type="Text"))
        if recipient in names:
            return chat_item

    raise ValueError(f"找不到聊天室「{recipient}」，請確認名稱與 LINE 左側清單顯示的名稱相同。")


def get_chat_list():
    lists = win.descendants(control_type="List")
    if not lists:
        raise RuntimeError("找不到 LINE 聊天清單。")
    return max(lists, key=lambda item: len(item.children()))


def send_message(text, recipient):
    win.set_focus()
    chat_item = find_chat(recipient)
    chat_item.click_input()
    time.sleep(0.5)
    edits = win.descendants(control_type="Edit")
    if not edits:
        raise RuntimeError("找不到訊息輸入欄位。")
    edit = edits[0]
    edit.click_input()
    send_keys(text)
    send_keys("{ENTER}")
    print(f"[{datetime.datetime.now()}] 已發送給「{recipient}」: {text}")


def send_messages(text, recipients):
    for recipient in recipients:
        send_message(text, recipient)


def send_to_top_chats(text, recipient_count):
    """從 LINE 左側聊天清單最上方開始，依序發送給指定數量的聊天室。"""
    chat_items = get_chat_list().children()
    if len(chat_items) < recipient_count:
        raise ValueError(f"聊天清單只找到 {len(chat_items)} 個項目，無法發送給前 {recipient_count} 個聊天室。")

    for index, chat_item in enumerate(chat_items[:recipient_count], start=1):
        win.set_focus()
        chat_item.click_input()
        time.sleep(0.5)
        edits = win.descendants(control_type="Edit")
        if not edits:
            raise RuntimeError("找不到訊息輸入欄位。")
        edits[0].click_input()
        send_keys(text)
        send_keys("{ENTER}")
        print(f"[{datetime.datetime.now()}] 已發送給清單第 {index} 個對話: {text}")


WEEKDAYS = {
    "星期一": "monday",
    "星期二": "tuesday",
    "星期三": "wednesday",
    "星期四": "thursday",
    "星期五": "friday",
    "星期六": "saturday",
    "星期日": "sunday",
}


def validate_time(value):
    datetime.datetime.strptime(value, "%H:%M")
    return value


def send_on_date(target_date, send_time, send_job):
    """僅在目標日期的指定時間發送；日期過期後取消這個工作。"""
    today = datetime.date.today()
    if today == target_date:
        send_job()
        return schedule.CancelJob
    if today > target_date:
        print(f"[{datetime.datetime.now()}] 已略過過期排程：{target_date} {send_time}")
        return schedule.CancelJob


def schedule_on_date(date_text, times, send_job):
    target_date = datetime.datetime.strptime(date_text, "%Y-%m-%d").date()
    for send_time in times:
        schedule.every().day.at(validate_time(send_time)).do(
            send_on_date, target_date=target_date, send_time=send_time, send_job=send_job
        )


def configure_schedule(config, send_job):
    schedule_type = config["type"]

    if schedule_type == "once":
        send_at = datetime.datetime.strptime(config["datetime"], "%Y-%m-%d %H:%M")
        schedule_on_date(send_at.strftime("%Y-%m-%d"), [send_at.strftime("%H:%M")], send_job)
    elif schedule_type == "daily":
        for send_time in config["times"]:
            schedule.every().day.at(validate_time(send_time)).do(send_job)
    elif schedule_type == "weekly":
        # weekday 可填單一星期；weekdays 可填多個星期。
        weekdays = config.get("weekdays")
        if weekdays is None:
            weekdays = [config["weekday"]]
        if not isinstance(weekdays, list) or not weekdays:
            raise ValueError("weekdays 必須是至少包含一個星期的清單。")
        for weekday_name in weekdays:
            weekday = WEEKDAYS.get(weekday_name.lower())
            if weekday is None:
                raise ValueError("weekday 必須是星期一至星期日。")
            for send_time in config["times"]:
                getattr(schedule.every(), weekday).at(validate_time(send_time)).do(
                    send_job
                )
    elif schedule_type == "one_day":
        schedule_on_date(config["date"], config["times"], send_job)
    else:
        raise ValueError("schedule.type 必須是 once、daily、weekly 或 one_day。")

# === 排程設定 ===
with open(JSON_PATH, "r", encoding="utf-8") as f:
    config_file = json.load(f)

# 支援原本的訊息陣列，或含有頂層「使用說明」與 messages 的設定檔。
messages = config_file.get("messages") if isinstance(config_file, dict) else config_file
if not isinstance(messages, list):
    raise ValueError("messages.json 必須是訊息陣列，或包含 messages 陣列的物件。")

for msg in messages:
    text = msg["message"]
    # 收件者可依名稱指定，或從清單最上方開始指定數量；兩種模式不可混用。
    recipients = msg.get("recipients")
    if recipients is None:
        legacy_recipient = msg.get("recipient")
        recipients = [legacy_recipient] if legacy_recipient else None
    recipient_count = msg.get("recipient_count")

    if recipients is not None and recipient_count is not None:
        raise ValueError("recipients 與 recipient_count 只能擇一使用。")
    if recipients is not None:
        if not isinstance(recipients, list) or not recipients or not all(isinstance(name, str) and name.strip() for name in recipients):
            raise ValueError("recipients 必須是至少包含一個聊天室名稱的清單。")
        send_job = partial(send_messages, text, recipients)
    elif isinstance(recipient_count, int) and recipient_count > 0:
        send_job = partial(send_to_top_chats, text, recipient_count)
    else:
        raise ValueError("每筆訊息必須設定 recipients 或大於 0 的 recipient_count。")

    if "schedule" in msg:
        configure_schedule(msg["schedule"], send_job)
    else:
        # 相容舊版格式：datetime 只使用時間，每日發送。
        send_time = datetime.datetime.strptime(msg["datetime"], "%Y-%m-%d %H:%M")
        schedule.every().day.at(send_time.strftime("%H:%M")).do(send_job)

print("排程已設定，等待執行...")

while True:
    schedule.run_pending()
    time.sleep(30)
