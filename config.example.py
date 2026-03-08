# config.example.py — шаблон настроек
# Скопируй в config.py и подставь свои данные:
#   copy config.example.py config.py
# Токен — @BotFather, chat_id — @userinfobot

# Путь к папке с изображениями для поиска на экране
IMAGES_DIR = "images"

# Настройки распознавания и задержек
BOT = {
    "confidence": 0.7,
    "delay": 1.0,
    "battle_result_delay": 15.0,
    "stats_interval_seconds": 3600,  # статистика в Telegram каждый час
    "hang_check_seconds": 20,       # если N сек нет действий — уведомление о зависании
    "notify_every_n_wins": 10,      # уведомление в Telegram каждую N-ю победу
    "daily_report_hour": 23,
}

TELEGRAM_CONFIG = {
    "enabled": True,
    "token": "СЮДА_ТОКЕН_ОТ_BOTFATHER",
    "chat_id": "СЮДА_ТВОЙ_CHAT_ID",
    "notify_on_error": True,
    "daily_report": True,
    "daily_report_time": "23:00",
}
