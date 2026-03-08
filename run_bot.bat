@echo off
cd /d "%~dp0"

title Battle Bot
echo.
echo  Battle Bot (Telegram + проверка зависания)
echo  Остановка: закройте это окно или Ctrl+C
echo.

py -3.9 game_bot_with_telegram.py
if errorlevel 1 (
    echo.
    echo  Ошибка запуска. Проверьте: Python 3.9, зависимости, config.py
    echo.
)

pause
