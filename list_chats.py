"""讀取 LINE 左側聊天清單，產生可用於 messages.json 的聊天室名稱。"""

import os
import time

from pywinauto import mouse
from pywinauto.application import Application


OUTPUT_PATH = "聊天室名稱.txt"
LINE_PATHS = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "LINE", "bin", "LineLauncher.exe"),
    os.path.join(os.environ.get("APPDATA", ""), "LINE", "bin", "LineLauncher.exe"),
]


def connect_line(retry=3, delay=5):
    for attempt in range(retry):
        try:
            return Application(backend="uia").connect(title_re="LINE")
        except Exception:
            if attempt == 0:
                line_path = next((path for path in LINE_PATHS if os.path.isfile(path)), None)
                if line_path:
                    Application(backend="uia").start(line_path)
            time.sleep(delay)
    raise RuntimeError("無法連線至 LINE，請確認 LINE 桌面版已開啟且保持登入。")


def chat_name(chat_item):
    """LINE 聊天列的第一個文字控制項是聊天室名稱。"""
    for text_element in chat_item.descendants(control_type="Text"):
        text = text_element.window_text().strip()
        if text:
            return text
    return ""


def get_chat_list(window):
    lists = window.descendants(control_type="List")
    if not lists:
        raise RuntimeError("找不到 LINE 聊天清單。")
    return max(lists, key=lambda item: len(item.children()))


def collect_chat_names(chat_list):
    names = []
    seen = set()
    no_new_rounds = 0

    # LINE 只會載入畫面附近的項目，因此捲動到底並逐段收集。
    while no_new_rounds < 3:
        new_count = 0
        for chat_item in chat_list.children():
            name = chat_name(chat_item)
            if name and name not in seen:
                seen.add(name)
                names.append(name)
                new_count += 1

        if new_count:
            no_new_rounds = 0
        else:
            no_new_rounds += 1

        rect = chat_list.rectangle()
        mouse.scroll(coords=(rect.mid_point().x, rect.mid_point().y), wheel_dist=-5)
        time.sleep(0.5)

    return names


def main():
    app = connect_line()
    window = app.window(title_re="LINE")
    window.set_focus()
    chat_list = get_chat_list(window)
    names = collect_chat_names(chat_list)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
        output_file.write("\n".join(names))
        if names:
            output_file.write("\n")

    print(f"已列出 {len(names)} 個聊天室：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
