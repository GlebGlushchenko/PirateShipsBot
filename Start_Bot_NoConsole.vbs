' Запуск бота без окна консоли (двойной клик — бот работает в фоне)
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "pyw -3.9 game_bot_with_telegram.py", 0, False
