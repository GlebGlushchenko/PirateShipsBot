"""
Telegram уведомления для игрового бота
"""
import requests
import threading
import time
from datetime import datetime
import json
import os
from queue import Queue
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token, chat_id, stats_file='telegram_stats.json'):
        """
        Инициализация Telegram уведомлений
        
        :param bot_token: Токен бота от @BotFather
        :param chat_id: Ваш chat_id (можно получить у @userinfobot)
        :param stats_file: Файл для сохранения статистики
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.stats_file = stats_file
        
        # Очередь сообщений для асинхронной отправки
        self.message_queue = Queue()
        self.running = True
        
        # Загружаем сохранённую статистику
        self.last_notification_time = {}
        self.notification_counts = self.load_stats()
        
        # Запускаем фоновый поток для отправки сообщений
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

        logger.info(f"TelegramNotifier инициализирован. Chat ID: {chat_id}")
    
    def _send_sync_message(self, text, parse_mode='HTML'):
        """Синхронная отправка сообщения (внутренний метод)"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.debug(f"Сообщение отправлено: {text[:50]}...")
                return True
            else:
                logger.error(f"Ошибка отправки: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Исключение при отправке: {e}")
            return False
    
    def _process_queue(self):
        """Фоновый процесс для отправки сообщений из очереди"""
        while self.running:
            try:
                if not self.message_queue.empty():
                    message = self.message_queue.get(timeout=1)
                    self._send_sync_message(message)
                    time.sleep(0.5)  # Защита от флуда
                else:
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Ошибка в process_queue: {e}")
                time.sleep(1)
    
    def send_message(self, text, important=False):
        """
        Отправка сообщения в Telegram
        
        :param text: Текст сообщения
        :param important: Если True - отправляет сразу, иначе через очередь
        """
        if important:
            # Важные сообщения отправляем сразу
            self._send_sync_message(text)
        else:
            # Обычные сообщения через очередь
            self.message_queue.put(text)
    
    def send_stats(self, stats):
        """Отправка текущей статистики"""
        win_rate = (stats['wins'] / stats['total_battles']) * 100 if stats['total_battles'] > 0 else 0
        
        message = f"""
📊 <b>ТЕКУЩАЯ СТАТИСТИКА</b>

⚔️ <b>БОИ:</b>
🏆 Побед: {stats['wins']}
💔 Поражений: {stats['losses']}
📈 Процент: {win_rate:.1f}%
🔢 Всего: {stats['total_battles']}

💰 <b>ЗОЛОТО:</b>
💎 Всего: {stats['gold']['total']:,}
📊 Среднее за победу: {stats['gold']['average_win']:.0f}
📉 Среднее за поражение: {stats['gold']['average_loss']:.0f}
📈 Макс победа: {stats['gold']['max_win']:,}
📉 Мин победа: {stats['gold']['min_win']:,}

🎮 <b>ПРОГРЕСС:</b>
⬆️ Уровней: {stats['level_ups']}
📉 Отказов: {stats['offers_declined']}

🖱️ <b>КЛИКИ:</b>
{self._format_clicks(stats['clicks'])}
"""
        self.send_message(message, important=True)
    
    def _format_clicks(self, clicks):
        """Форматирование статистики кликов"""
        result = []
        for key, value in clicks.items():
            if value > 0:
                emoji = {
                    'prodolzhit': '▶️',
                    'otkazatsya': '❌',
                    'zabrat': '🎁',
                    'click_to_continue': '⏭️',
                    'v_boy_2': '⚔️',
                    'v_boy': '⚔️'
                }.get(key, '🔘')
                result.append(f"{emoji} {key}: {value}")
        return '\n'.join(result) if result else "Нет данных"
    
    def notify_every_nth_win(self, win_number, stats):
        """Краткое уведомление каждую N-ю победу (только статистика)."""
        win_rate = (stats['wins'] / stats['total_battles']) * 100 if stats['total_battles'] > 0 else 0
        message = (
            f"<b>Победа #{win_number}</b>\n"
            f"⚔️ Боёв: {stats['total_battles']} | 🏆 {stats['wins']} | 💔 {stats['losses']} | 📈 {win_rate:.1f}%\n"
            f"💰 Золото: {stats['gold']['total']:,}"
        )
        self.send_message(message, important=True)

    
    def send_error_report(self, error_msg):
        """Отправка отчёта об ошибке"""
        message = f"""
⚠️ <b>ОБНАРУЖЕНА ОШИБКА</b>

Текст ошибки:
<code>{error_msg}</code>

Время: {datetime.now().strftime('%H:%M:%S')}
"""
        self.send_message(message, important=True)
    
    def send_daily_report(self, stats):
        """Ежедневный отчёт (можно вызывать раз в сутки)"""
        win_rate = (stats['wins'] / stats['total_battles']) * 100 if stats['total_battles'] > 0 else 0
        
        message = f"""
📅 <b>ЕЖЕДНЕВНЫЙ ОТЧЁТ</b>
{datetime.now().strftime('%d.%m.%Y')}

<b>Итоги дня:</b>
⚔️ Боёв: {stats['total_battles']}
🏆 Побед: {stats['wins']}
💔 Поражений: {stats['losses']}
📈 Процент побед: {win_rate:.1f}%
💰 Заработано всего: {stats['gold']['total']:,}

<b>Золото за день:</b>
📊 Среднее за победу: {stats['gold']['average_win']:.0f}
📉 Среднее за поражение: {stats['gold']['average_loss']:.0f}
🏆 Рекорд победы: {stats['gold']['max_win']:,}
💔 Антирекорд: {stats['gold']['min_win']:,}

<b>Прогресс за день:</b>
⬆️ Уровней: {stats['level_ups']}
📉 Отказов: {stats['offers_declined']}

Хорошей игры завтра! 🌙
"""
        self.send_message(message, important=True)
    
    def send_photo(self, image_path, caption=""):
        """Отправка скриншота"""
        try:
            url = f"{self.base_url}/sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.chat_id, 'caption': caption}
                response = requests.post(url, files=files, data=data)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            return False
    
    def save_stats(self):
        """Сохранение статистики уведомлений"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.notification_counts, f)
        except:
            pass
    
    def load_stats(self):
        """Загрузка статистики уведомлений"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def notify_hang(self, idle_seconds, screenshot_path=None):
        """Уведомление о возможном зависании. Если передан screenshot_path — отправляет скриншот с подписью."""
        message = (
            f"⚠️ ВОЗМОЖНОЕ ЗАВИСАНИЕ\n\n"
            f"Более {idle_seconds} сек не было ни одного действия.\n"
            f"Проверьте, не завис ли бот или игра.\n\n"
            f"🕐 {datetime.now().strftime('%H:%M:%S')}"
        )
        if screenshot_path and os.path.exists(screenshot_path):
            self.send_photo(screenshot_path, caption=message)
        else:
            self.send_message(message, important=True)

    def stop(self, send_stopped_message=False):
        """Остановка уведомлений. send_stopped_message=False — не слать «Бот остановлен» (если уже отправили итог)."""
        self.running = False
        self.save_stats()
        if send_stopped_message:
            self.send_message("🔴 Бот остановлен", important=True)
        logger.info("TelegramNotifier остановлен")