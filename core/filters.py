"""
Фильтры для извлечения и обработки данных о пиве.
"""
import re
from typing import Optional
import config


def extract_beer_style(text: str) -> Optional[str]:
    """
    Извлечь стиль пива из текста.
    
    Args:
        text: Текст для анализа
        
    Returns:
        Optional[str]: Найденный стиль или None
    """
    if not text or not isinstance(text, str):
        return None
    
    text_upper = text.upper()
    
    # Сортируем стили по длине (от длинных к коротким) для правильного поиска
    # Например, "Imperial Stout" должен находиться раньше "Stout"
    sorted_styles = sorted(config.BEER_STYLES, key=len, reverse=True)
    
    # Поиск по известным стилям
    for style in sorted_styles:
        if style.upper() in text_upper:
            return style
    
    return None


def extract_brewery_from_filename(filename: str) -> Optional[str]:
    """
    Извлечь название пивоварни из имени файла.
    
    Args:
        filename: Имя файла
        
    Returns:
        Optional[str]: Название пивоварни или None
    """
    if not filename:
        return None
    
    # Убираем расширение
    name = filename.lower()
    for ext in ['.xlsx', '.xls', '.csv']:
        name = name.replace(ext, '')
    
    # Известные пивоварни (можно расширить)
    breweries = [
        "AF Brew", "Zagovor", "Salden's", "Балтика", "Пивоваренный Дом",
        "BrewDog", "Craft Republic", "Лаборатория", "Selfmade"
    ]
    
    for brewery in breweries:
        if brewery.lower() in name:
            return brewery
    
    # Попытка извлечь из паттернов
    patterns = [
        r"([A-Za-zА-Яа-яЁё\s]+)_price",
        r"([A-Za-zА-Яа-яЁё\s]+)_прайс",
        r"price_([A-Za-zА-Яа-яЁё\s]+)",
        r"прайс_([A-Za-zА-Яа-яЁё\s]+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name)
        if match:
            return match.group(1).strip().title()
    
    return None


def extract_volume(text: str) -> Optional[str]:
    """
    Извлечь объем из текста.
    
    Args:
        text: Текст для анализа
        
    Returns:
        Optional[str]: Объем в стандартизированном виде
    """
    if not text:
        return None
    
    # Если передано число (литраж кеги)
    try:
        volume_num = float(text)
        # Если >= 15 литров - это ПЭТ-кега
        if volume_num >= 15:
            return f"{int(volume_num)} л (ПЭТ-кега)"
        elif volume_num > 0:
            return f"{volume_num} л"
    except (ValueError, TypeError):
        pass
    
    if not isinstance(text, str):
        return None
    
    text_original = str(text)
    text = text_original.lower()
    
    # Удаляем переносы строк для поиска
    text_clean = text.replace('\n', ' ').replace('\r', ' ')
    
    # Проверяем, есть ли упоминание кеги (включая ПЭТ-кеги)
    is_keg = 'кег' in text_clean or 'keg' in text_clean or 'пэт' in text_clean or 'pet' in text_clean
    
    # Определение типа тары
    container_type = None
    if 'бутылка' in text_clean or 'bottle' in text_clean or 'бут' in text_clean:
        container_type = 'бутылка'
    elif 'банка' in text_clean or 'can' in text_clean or 'банку' in text_clean or 'ж/б' in text_clean:
        container_type = 'банка'
    
    # Паттерны для литров и дробных чисел (0,33 0,5 и т.д.)
    liter_patterns = [
        r'(\d+(?:[.,]\d+)?)\s*л(?:итр)?',
        r'(\d+(?:[.,]\d+)?)\s*l(?:iter)?',
        r'(\d[.,]\d+)',  # Дробные числа типа 0,33 или 0.5
    ]
    
    # Ищем в очищенном тексте (без переносов)
    for pattern in liter_patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            volume = match.group(1).replace(',', '.')
            if is_keg:
                return f"{volume} л (кега)"
            elif container_type:
                return f"{volume} л ({container_type})"
            return f"{volume} л"
    
    # Паттерны для миллилитров
    ml_patterns = [
        r'(\d+)\s*мл',
        r'(\d+)\s*ml',
    ]
    
    for pattern in ml_patterns:
        match = re.search(pattern, text_clean, re.IGNORECASE)
        if match:
            ml = int(match.group(1))
            liters = ml / 1000
            if is_keg:
                return f"{liters} л (кега)"
            elif container_type:
                return f"{liters} л ({container_type})"
            return f"{liters} л"
    
    # Если есть упоминание кеги, но нет объема - ищем число
    if is_keg:
        # ПЭТ-кеги
        if 'пэт 30' in text_clean or 'pet 30' in text_clean:
            return "30 л (ПЭТ-кега)"
        elif 'пэт 20' in text_clean or 'pet 20' in text_clean:
            return "20 л (ПЭТ-кега)"
        # Обычные кеги
        elif '30' in text_clean:
            return "30 л (кега)"
        elif '50' in text_clean:
            return "50 л (кега)"
        elif '20' in text_clean:
            return "20 л (кега)"
        else:
            return "кега"
    
    return None


def extract_price(text: str, volume_text: Optional[str] = None) -> Optional[str]:
    """
    Извлечь цену из текста.
    
    Args:
        text: Текст с ценой
        volume_text: Текст с объемом (для расчета цены за литр)
        
    Returns:
        Optional[str]: Цена в стандартизированном виде
    """
    if not text:
        return None
    
    text = str(text)
    
    # Паттерны для цены
    price_patterns = [
        r'(\d+(?:[.,]\d+)?)\s*(?:руб|₽|rub)?',
        r'(\d+(?:[.,]\d+)?)',
    ]
    
    price = None
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            price_value = match.group(1).replace(',', '.')
            price = f"{price_value} руб."
            break
    
    # Не добавляем расчет цены за литр - пользователь сам это видит
    return price


def clean_text(text) -> str:
    """
    Очистить текст от лишних символов и пробелов.
    
    Args:
        text: Текст для очистки
        
    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""
    
    text = str(text).strip()
    
    # Если текст многострочный - берём только первую строку (это название)
    # Остальное - описание
    if '\n' in text:
        text = text.split('\n')[0].strip()
    
    # Удаление множественных пробелов
    text = re.sub(r'\s+', ' ', text)
    
    # Удаление спецсимволов
    text = text.replace('\r', ' ').replace('\t', ' ')
    
    return text.strip()

