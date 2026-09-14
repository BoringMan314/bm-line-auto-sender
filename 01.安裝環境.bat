@echo off
setlocal
chcp 950 >nul
cd /d "%~dp0"

echo 正在安裝 Python 相依套件...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo 安裝失敗。請確認已安裝 Python，且網路連線正常。
    pause
    exit /b 1
)

echo.
echo 安裝完成。
pause
