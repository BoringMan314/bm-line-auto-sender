@echo off
setlocal
chcp 950 >nul
cd /d "%~dp0"

python list_chats.py
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo 產生聊天室清單失敗，請確認 LINE 已開啟並登入。
) else (
    echo.
    echo 已產生「聊天室名稱.txt」。
)

echo.
pause
exit /b %EXIT_CODE%
