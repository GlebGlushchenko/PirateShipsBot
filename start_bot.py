import pyautogui
import time
import random  # Для симуляции получения золота (в реальности нужно будет распознавать цифры)

# Настройки
CONFIDENCE = 0.7 
DELAY = 1.0      
BATTLE_RESULT_DELAY = 15.0

# Статистика
stats = {
    'wins': 0,
    'losses': 0,
    'total_battles': 0,
    'level_ups': 0,
    'offers_declined': 0,
    'gold': {
        'total': 0,
        'from_wins': 0,
        'from_losses': 0,
        'average_win': 0,
        'average_loss': 0,
        'min_win': 10000,  # Для подсчета мин/макс
        'max_win': 0,
        'min_loss': 2000,  # Для подсчета мин/макс
        'max_loss': 0
    },
    'clicks': {
        'prodolzhit': 0,
        'otkazatsya': 0,
        'zabrat': 0,
        'click_to_continue': 0,
        'v_boy_2': 0,
        'v_boy': 0
    }
}

last_battle_result_time = 0
last_battle_result_type = None
last_click_time = 0

# В реальности здесь нужно будет распознавать цифры золота на экране
# Пока используем заглушку с рандомом для тестирования
def get_gold_amount():
    """
    Функция для получения количества золота.
    В реальности должна анализировать экран и извлекать цифры.
    Сейчас для теста возвращает случайные значения.
    """
    # TODO: Заменить на реальное распознавание цифр с экрана
    # Например, с помощью pytesseract или поиска цифр по шаблонам
    
    # Для теста возвращаем реалистичные значения
    if last_battle_result_type == 'win':
        return random.randint(9000, 10000)
    else:
        return random.randint(1000, 1600)

def check_image(image_path):
    """Проверяет наличие картинки без клика и без вывода ошибок"""
    try:
        return pyautogui.locateOnScreen(image_path, confidence=CONFIDENCE) is not None
    except:
        return False

def click_if_exists(image_path, name, stat_key=None, post_delay=1.0):
    """Ищет и кликает ТОЛЬКО если картинка найдена"""
    global last_click_time, stats
    
    try:
        location = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE)
        if location:
            pyautogui.click(location)
            print(f"✅ Действие: {name}")
            last_click_time = time.time()
            
            if stat_key and stat_key in stats['clicks']:
                stats['clicks'][stat_key] += 1
            
            time.sleep(post_delay)
            return True
        return False
    except:
        return False

def handle_prodolzhit():
    """Специальная обработка кнопки Продолжить"""
    if not check_image('prodolzhit.png'):
        return False
    
    if check_image('slovo_uroven.png'):
        stats['level_ups'] += 1
        print(f"\n{'🎉'*10}")
        print(f"ПОВЫШЕНИЕ УРОВНЯ #{stats['level_ups']}!")
        print(f"{'🎉'*10}\n")
        return click_if_exists('prodolzhit.png', 'ПОВЫШЕНИЕ УРОВНЯ', 'prodolzhit', 3.5)
    else:
        return click_if_exists('prodolzhit.png', 'Обычное ПРОДОЛЖИТЬ', 'prodolzhit', 1.5)

def handle_otkazatsya():
    """Специальная обработка кнопки Отказаться"""
    if not check_image('otkazatsya.png'):
        return False
    
    stats['offers_declined'] += 1
    return click_if_exists('otkazatsya.png', 'ОТКАЗАТЬСЯ', 'otkazatsya', 1.5)

def update_battle_stats():
    """Проверяет экран победы/поражения и обновляет статистику с золотом"""
    global stats, last_battle_result_time, last_battle_result_type
    
    current_time = time.time()
    
    if current_time - last_click_time < 3.0:
        return False
    
    if check_image('win.png'):
        if current_time - last_battle_result_time > BATTLE_RESULT_DELAY or last_battle_result_type != 'win':
            # Получаем золото за победу
            gold_earned = get_gold_amount()
            
            # Обновляем статистику
            stats['wins'] += 1
            stats['total_battles'] += 1
            stats['gold']['total'] += gold_earned
            stats['gold']['from_wins'] += gold_earned
            
            # Обновляем мин/макс для побед
            stats['gold']['min_win'] = min(stats['gold']['min_win'], gold_earned)
            stats['gold']['max_win'] = max(stats['gold']['max_win'], gold_earned)
            
            # Пересчитываем среднее за победу
            stats['gold']['average_win'] = stats['gold']['from_wins'] / stats['wins']
            
            last_battle_result_time = current_time
            last_battle_result_type = 'win'
            
            print_battle_result('ПОБЕДА', gold_earned)
            time.sleep(5.0)
        return True
        
    elif check_image('lose.png'):
        if current_time - last_battle_result_time > BATTLE_RESULT_DELAY or last_battle_result_type != 'lose':
            # Получаем золото за поражение
            gold_earned = get_gold_amount()
            
            # Обновляем статистику
            stats['losses'] += 1
            stats['total_battles'] += 1
            stats['gold']['total'] += gold_earned
            stats['gold']['from_losses'] += gold_earned
            
            # Обновляем мин/макс для поражений
            stats['gold']['min_loss'] = min(stats['gold']['min_loss'], gold_earned)
            stats['gold']['max_loss'] = max(stats['gold']['max_loss'], gold_earned)
            
            # Пересчитываем среднее за поражение
            stats['gold']['average_loss'] = stats['gold']['from_losses'] / stats['losses']
            
            last_battle_result_time = current_time
            last_battle_result_type = 'lose'
            
            print_battle_result('ПОРАЖЕНИЕ', gold_earned)
            time.sleep(5.0)
        return True
    
    return False

def print_battle_result(result_type, gold_earned):
    """Выводит результат боя с информацией о золоте"""
    win_rate = (stats['wins'] / stats['total_battles']) * 100 if stats['total_battles'] > 0 else 0
    
    emoji = "💚" if result_type == "ПОБЕДА" else "💔"
    
    print(f"\n{'='*60}")
    print(f"{emoji} {result_type}!")
    print(f"{'='*60}")
    print(f"💰 Золото получено: {gold_earned:,}")
    print(f"💎 Всего золота: {stats['gold']['total']:,}")
    print(f"\n📊 Статистика боёв:")
    print(f"   🏆 Побед: {stats['wins']} | 💔 Поражений: {stats['losses']}")
    print(f"   📈 Процент побед: {win_rate:.1f}%")
    print(f"\n💰 Статистика золота:")
    print(f"   За победы: {stats['gold']['from_wins']:,} (среднее: {stats['gold']['average_win']:.0f})")
    print(f"   За поражения: {stats['gold']['from_losses']:,} (среднее: {stats['gold']['average_loss']:.0f})")
    print(f"   Диапазон побед: {stats['gold']['min_win']:,} - {stats['gold']['max_win']:,}")
    print(f"   Диапазон поражений: {stats['gold']['min_loss']:,} - {stats['gold']['max_loss']:,}")
    print(f"\n🎮 Прогресс:")
    print(f"   ⬆️ Повышений уровня: {stats['level_ups']}")
    print(f"   📉 Отказов: {stats['offers_declined']}")
    print(f"{'='*60}\n")

def print_detailed_stats():
    """Выводит детальную статистику"""
    win_rate = (stats['wins'] / stats['total_battles']) * 100 if stats['total_battles'] > 0 else 0
    
    print(f"\n{'═'*60}")
    print(f"📊 ДЕТАЛЬНАЯ СТАТИСТИКА")
    print(f"{'═'*60}")
    
    print(f"\n⚔️  БОИ:")
    print(f"   🏆 Побед: {stats['wins']}")
    print(f"   💔 Поражений: {stats['losses']}")
    print(f"   📈 Процент побед: {win_rate:.1f}%")
    print(f"   🔢 Всего боёв: {stats['total_battles']}")
    
    print(f"\n💰 ЗОЛОТО:")
    print(f"   💎 Всего заработано: {stats['gold']['total']:,}")
    print(f"   📊 За победы: {stats['gold']['from_wins']:,} (среднее: {stats['gold']['average_win']:.0f})")
    print(f"   📉 За поражения: {stats['gold']['from_losses']:,} (среднее: {stats['gold']['average_loss']:.0f})")
    print(f"   📈 Диапазон побед: {stats['gold']['min_win']:,} - {stats['gold']['max_win']:,}")
    print(f"   📉 Диапазон поражений: {stats['gold']['min_loss']:,} - {stats['gold']['max_loss']:,}")
    
    print(f"\n🎮 ПРОГРЕСС:")
    print(f"   ⬆️ Повышений уровня: {stats['level_ups']}")
    print(f"   📉 Отказов от предложений: {stats['offers_declined']}")
    
    if stats['clicks']:
        print(f"\n🖱️ КЛИКИ:")
        for key, value in stats['clicks'].items():
            if value > 0:
                print(f"   {key}: {value}")
    
    print(f"{'═'*60}\n")

print("=== БОТ ЗАПУЩЕН (С подсчетом золота) ===")
print("Нажмите Ctrl+C для остановки\n")

try:
    battle_result_cooldown = 0
    last_check_time = time.time()
    
    while True:
        current_time = time.time()
        
        # Проверка результатов боя
        if current_time - battle_result_cooldown > 5.0:
            if update_battle_stats():
                battle_result_cooldown = current_time
                continue
        
        # Приоритет 1: Продолжить
        if handle_prodolzhit():
            last_check_time = current_time
            continue
            
        # Приоритет 2: Отказаться
        if handle_otkazatsya():
            last_check_time = current_time
            continue
            
        # Приоритет 3: Забрать награду
        if click_if_exists('zabrat.png', 'Забрать награду', 'zabrat', 2.0):
            last_check_time = current_time
            continue
            
        # Приоритет 4: Пропуск текста
        if click_if_exists('click_to_continue.png', 'Пропуск текста', 'click_to_continue', 1.5):
            last_check_time = current_time
            continue
            
        # Приоритет 5: В бой (вторая)
        if click_if_exists('v_boy_2.png', 'В бой (вторая)', 'v_boy_2', 1.0):
            last_check_time = current_time
            continue
            
        # Приоритет 6: В бой (основная)
        if click_if_exists('v_boy.png', 'В бой (основная)', 'v_boy', 1.0):
            last_check_time = current_time
            continue
        
        time.sleep(DELAY)

except KeyboardInterrupt:
    print("\n" + "="*70)
    print("🚫 БОТ ОСТАНОВЛЕН")
    print("="*70)
    print_detailed_stats()
    print("="*70)