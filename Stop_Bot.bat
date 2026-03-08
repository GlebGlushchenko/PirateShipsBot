@echo off
cd /d "%~dp0"
title Остановка бота

echo.
echo  Останавливаю Battle Bot (процесс без консоли)...
echo.

REM Убиваем только процесс с game_bot_with_telegram.py в командной строке
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"CommandLine LIKE '%%game_bot_with_telegram%%'\" | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

if errorlevel 1 (
    echo  Процесс не найден или уже остановлен.
) else (
    echo  Бот остановлен.
)

echo.
pause
