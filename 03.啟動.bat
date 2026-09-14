@echo off
setlocal
chcp 950 >nul
cd /d "%~dp0"

REM 如需確認已安裝套件的版本，取消下方兩行註解。
REM python -m pip show pywinauto
REM python -m pip show schedule

python .\main.py
