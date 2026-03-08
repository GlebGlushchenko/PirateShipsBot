@echo off
echo Trying to install using 'py' command...
py -m pip install pyautogui opencv-python pillow
echo.
echo If it failed, trying 'python' command...
python -m pip install pyautogui opencv-python pillow
echo.
echo Check the text above. If it says "Successfully installed", you are good!
pause