"""
Игровой бот с уведомлениями в Telegram.
Настройки берутся из config.py. Проверка на зависание: при отсутствии действий 20 сек — уведомление в Telegram.
"""
import pyautogui
import time
import random
import os
import tempfile
from datetime import datetime

from config import BOT, TELEGRAM_CONFIG, IMAGES_DIR

try:
    from telegram_notifier import TelegramNotifier
    TELEGRAM_AVAILABLE = True
except ImportError:
    print("⚠️ Модуль telegram_notifier не найден. Уведомления отключены.")
    TELEGRAM_AVAILABLE = False

# Константы из config
CONFIDENCE = BOT["confidence"]
DELAY = BOT["delay"]
BATTLE_RESULT_DELAY = BOT["battle_result_delay"]
STATS_INTERVAL = BOT["stats_interval_seconds"]
HANG_CHECK_SECONDS = BOT["hang_check_seconds"]
DAILY_REPORT_HOUR = BOT["daily_report_hour"]
NOTIFY_EVERY_N_WINS = BOT.get("notify_every_n_wins", 10)


def image_path(name):
    """Путь к изображению в папке IMAGES_DIR."""
    return os.path.join(IMAGES_DIR, name)


# ===== СТАТИСТИКА =====
stats = {
    "wins": 0,
    "losses": 0,
    "total_battles": 0,
    "level_ups": 0,
    "offers_declined": 0,
    "gold": {
        "total": 0,
        "from_wins": 0,
        "from_losses": 0,
        "average_win": 0,
        "average_loss": 0,
        "min_win": 10000,
        "max_win": 0,
        "min_loss": 2000,
        "max_loss": 0,
    },
    "clicks": {
        "prodolzhit": 0,
        "otkazatsya": 0,
        "zabrat": 0,
        "click_to_continue": 0,
        "v_boy_2": 0,
        "v_boy": 0,
    },
}

# Состояние цикла
last_battle_result_time = 0
last_battle_result_type = None
last_click_time = 0
last_activity_time = 0
last_hang_notify_time = None
last_daily_report_time = 0
last_stats_print = 0
start_time = datetime.now()

# ===== TELEGRAM =====
telegram = None
if TELEGRAM_AVAILABLE and TELEGRAM_CONFIG.get("enabled"):
    try:
        telegram = TelegramNotifier(
            TELEGRAM_CONFIG["token"],
            TELEGRAM_CONFIG["chat_id"],
        )
        print("✅ Telegram подключен")
        telegram.send_message(
            f"🚀 Бот запущен. Следите за уведомлениями.\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            important=True,
        )
    except Exception as e:
        print(f"❌ Ошибка Telegram: {e}")
        telegram = None


def mark_activity():
    """Вызывать при любом успешном действии (клик, результат боя)."""
    global last_activity_time, last_hang_notify_time
    last_activity_time = time.time()
    last_hang_notify_time = None


def get_gold_amount():
    if last_battle_result_type == "win":
        return random.randint(9000, 10000)
    return random.randint(1000, 1600)


def check_image(name):
    try:
        return pyautogui.locateOnScreen(image_path(name), confidence=CONFIDENCE) is not None
    except Exception:
        return False


def click_if_exists(img_name, action_name, stat_key=None, post_delay=1.0):
    global last_click_time, stats
    try:
        loc = pyautogui.locateCenterOnScreen(image_path(img_name), confidence=CONFIDENCE)
        if loc:
            pyautogui.click(loc)
            print(f"✅ {action_name}")
            last_click_time = time.time()
            mark_activity()
            if stat_key and stat_key in stats["clicks"]:
                stats["clicks"][stat_key] += 1
            time.sleep(post_delay)
            return True
        return False
    except Exception:
        return False


def handle_prodolzhit():
    if not check_image("prodolzhit.png"):
        return False
    if check_image("slovo_uroven.png"):
        stats["level_ups"] += 1
        print(f"\n{'🎉'*10}\nПОВЫШЕНИЕ УРОВНЯ #{stats['level_ups']}!\n{'🎉'*10}\n")
        return click_if_exists("prodolzhit.png", "ПОВЫШЕНИЕ УРОВНЯ", "prodolzhit", 3.5)
    return click_if_exists("prodolzhit.png", "ПРОДОЛЖИТЬ", "prodolzhit", 1.5)


def handle_otkazatsya():
    if not check_image("otkazatsya.png"):
        return False
    stats["offers_declined"] += 1
    return click_if_exists("otkazatsya.png", "ОТКАЗАТЬСЯ", "otkazatsya", 1.5)


def update_battle_stats():
    global stats, last_battle_result_time, last_battle_result_type
    now = time.time()
    if now - last_click_time < 3.0:
        return False
    if check_image("win.png"):
        if now - last_battle_result_time > BATTLE_RESULT_DELAY or last_battle_result_type != "win":
            gold_earned = get_gold_amount()
            stats["wins"] += 1
            stats["total_battles"] += 1
            stats["gold"]["total"] += gold_earned
            stats["gold"]["from_wins"] += gold_earned
            stats["gold"]["min_win"] = min(stats["gold"]["min_win"], gold_earned)
            stats["gold"]["max_win"] = max(stats["gold"]["max_win"], gold_earned)
            stats["gold"]["average_win"] = stats["gold"]["from_wins"] / stats["wins"]
            last_battle_result_time = now
            last_battle_result_type = "win"
            mark_activity()
            print_battle_result("ПОБЕДА", gold_earned)
            if telegram and stats["wins"] % NOTIFY_EVERY_N_WINS == 0:
                telegram.notify_every_nth_win(stats["wins"], stats)
            time.sleep(5.0)
        return True
    if check_image("lose.png"):
        if now - last_battle_result_time > BATTLE_RESULT_DELAY or last_battle_result_type != "lose":
            gold_earned = get_gold_amount()
            stats["losses"] += 1
            stats["total_battles"] += 1
            stats["gold"]["total"] += gold_earned
            stats["gold"]["from_losses"] += gold_earned
            stats["gold"]["min_loss"] = min(stats["gold"]["min_loss"], gold_earned)
            stats["gold"]["max_loss"] = max(stats["gold"]["max_loss"], gold_earned)
            stats["gold"]["average_loss"] = stats["gold"]["from_losses"] / stats["losses"]
            last_battle_result_time = now
            last_battle_result_type = "lose"
            mark_activity()
            print_battle_result("ПОРАЖЕНИЕ", gold_earned)
            time.sleep(5.0)
        return True
    return False


def print_battle_result(result_type, gold_earned):
    win_rate = (stats["wins"] / stats["total_battles"]) * 100 if stats["total_battles"] else 0
    emoji = "💚" if result_type == "ПОБЕДА" else "💔"
    print(f"\n{'='*60}\n{emoji} {result_type}!\n{'='*60}")
    print(f"💰 Золото: {gold_earned:,} | 💎 Всего: {stats['gold']['total']:,}")
    print(f"🏆 Побед: {stats['wins']} | 💔 Поражений: {stats['losses']} | 📈 {win_rate:.1f}%")
    print(f"{'='*60}\n")


def print_detailed_stats():
    win_rate = (stats["wins"] / stats["total_battles"]) * 100 if stats["total_battles"] else 0
    uptime = datetime.now() - start_time
    print(f"\n{'═'*60}\n📊 ДЕТАЛЬНАЯ СТАТИСТИКА\n{'═'*60}")
    print(f"⚔️ Боёв: {stats['total_battles']} | 🏆 {stats['wins']} | 💔 {stats['losses']} | 📈 {win_rate:.1f}%")
    print(f"💰 Золото: {stats['gold']['total']:,}")
    print(f"⬆️ Уровней: {stats['level_ups']} | 📉 Отказов: {stats['offers_declined']}")
    print(f"⏱️ Время работы: {str(uptime).split('.')[0]}\n{'═'*60}\n")


def check_daily_report():
    global last_daily_report_time
    now = time.time()
    if datetime.now().hour == DAILY_REPORT_HOUR and now - last_daily_report_time > 3600:
        if telegram and TELEGRAM_CONFIG.get("daily_report"):
            telegram.send_daily_report(stats)
            last_daily_report_time = now


def check_hang_and_notify():
    """Если долго не было действий — скриншот экрана и уведомление в Telegram (раз за период)."""
    global last_hang_notify_time
    now = time.time()
    if last_activity_time == 0:
        return
    idle = now - last_activity_time
    if idle < HANG_CHECK_SECONDS:
        return
    if last_hang_notify_time is not None and (now - last_hang_notify_time) < HANG_CHECK_SECONDS * 2:
        return
    last_hang_notify_time = now
    if telegram:
        screenshot_path = None
        try:
            fd, screenshot_path = tempfile.mkstemp(suffix=".png", prefix="hang_")
            os.close(fd)
            pyautogui.screenshot(screenshot_path)
            telegram.notify_hang(int(idle), screenshot_path=screenshot_path)
        except Exception as e:
            print(f"Скриншот при зависании не удался: {e}")
            telegram.notify_hang(int(idle))
        finally:
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    os.unlink(screenshot_path)
                except OSError:
                    pass


# ===== ГЛАВНЫЙ ЦИКЛ =====
# Инициализация времени активности после старта
mark_activity()

print("=== БОТ ЗАПУЩЕН (Telegram + проверка зависания) ===")
print("Остановка: Ctrl+C\n")

try:
    battle_result_cooldown = 0
    last_stats_print = time.time()

    while True:
        now = time.time()

        if now - last_stats_print > STATS_INTERVAL:
            print_detailed_stats()
            if telegram:
                telegram.send_stats(stats)
            last_stats_print = now

        check_daily_report()
        check_hang_and_notify()

        if now - battle_result_cooldown > 5.0 and update_battle_stats():
            battle_result_cooldown = now
            continue

        if handle_prodolzhit():
            continue
        if handle_otkazatsya():
            continue
        if click_if_exists("zabrat.png", "Забрать награду", "zabrat", 2.0):
            continue
        if click_if_exists("click_to_continue.png", "Пропуск текста", "click_to_continue", 1.5):
            continue
        if click_if_exists("v_boy_2.png", "В бой (вторая)", "v_boy_2", 1.0):
            continue
        if click_if_exists("v_boy.png", "В бой (основная)", "v_boy", 1.0):
            continue

        time.sleep(DELAY)

except KeyboardInterrupt:
    print("\n" + "=" * 70 + "\n🚫 БОТ ОСТАНОВЛЕН\n" + "=" * 70)
    print_detailed_stats()

    if telegram:
        uptime = datetime.now() - start_time
        final_message = (
            "🛑 <b>БОТ ОСТАНОВЛЕН</b>\n\n"
            f"⚔️ Боёв: {stats['total_battles']} | 🏆 {stats['wins']} | 💔 {stats['losses']}\n"
            f"💰 Золото: {stats['gold']['total']:,}\n"
            f"⬆️ Уровней: {stats['level_ups']}\n"
            f"⏱️ Время работы: {str(uptime).split('.')[0]}\n\n"
            "До новых побед! 🎮"
        )
        telegram.send_message(final_message, important=True)
        telegram.stop(send_stopped_message=False)

    print("=" * 70)
