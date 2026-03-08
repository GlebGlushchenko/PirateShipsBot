@echo off
cd /d "%~dp0"
title Установка зависимостей — Battle Bot

echo.
echo  Устанавливаю библиотеки из requirements.txt...
echo  (pyautogui, opencv-python, Pillow, requests)
echo.

py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  Пробую через python...
    python -m pip install -r requirements.txt
)

echo.
echo  Готово. Запускай run_bot.bat или Start_Bot_NoConsole.vbs
echo.
pause
