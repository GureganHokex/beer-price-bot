"""
ML-классификатор для определения типа колонок в Excel.
"""
import pickle
from typing import Optional
from pathlib import Path
import config


class ColumnDetector:
    """Детектор типов колонок с использованием ML."""
    
    def __init__(self):
        """Инициализация детектора."""
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Загрузить обученную модель."""
        if config.COLUMN_CLASSIFIER_PATH.exists():
            with open(config.COLUMN_CLASSIFIER_PATH, 'rb') as f:
                self.model = pickle.load(f)
        else:
            print(f"Модель не найдена: {config.COLUMN_CLASSIFIER_PATH}")
            print("Запустите ml/train_detector.py для обучения модели")
    
    def detect_column_type(self, column_name: str) -> str:
        """
        Определить тип колонки по её названию.
        
        Args:
            column_name: Название колонки
            
        Returns:
            str: Тип колонки (BREWERY, NAME, STYLE, VOLUME, PRICE, IGNORE)
        """
        if not column_name or not isinstance(column_name, str):
            return "IGNORE"
        
        # Очистка названия
        cleaned_name = str(column_name).strip()
        
        if not cleaned_name:
            return "IGNORE"
        
        # ЯВНО определяем важные колонки ДО ML-модели (точные совпадения)
        cleaned_lower = cleaned_name.lower()
        
        # PRICE - любое упоминание цены (ПЕРВЫМ!), но НЕ "сумма"
        # Включаем "цена за литр", "цена за шт" и т.д.
        if 'цена' in cleaned_lower and 'сумма' not in cleaned_lower:
            return "PRICE"
        if 'price' in cleaned_lower or 'стоимость' in cleaned_lower:
            return "PRICE"
        
        # BREWERY - точные совпадения
        if cleaned_lower in ['пивоварня', 'brewery', 'производитель']:
            return "BREWERY"
        
        # NAME - точные совпадения (но НЕ "наличие"!)
        if cleaned_lower in ['название', 'наименование', 'name', 'номенклатура']:
            return "NAME"
        
        # STYLE - точные совпадения
        if cleaned_lower in ['стиль', 'style', 'сорт']:
            return "STYLE"
        
        # VOLUME - точные совпадения
        if cleaned_lower in ['объем', 'объём', 'volume', 'тип тары', 'тара', 'вид упаковки', 'упаковка', 'тип фасовки', 'фасовка', 'литраж']:
            return "VOLUME"
        if 'тара' in cleaned_lower or 'упаковк' in cleaned_lower or 'фасовк' in cleaned_lower or 'литраж' in cleaned_lower:
            return "VOLUME"
        
        # ЯВНО игнорируем служебные и технические колонки
        ignore_columns = [
            'этикетка', 'etiquette', 'label', 'картинка', 'фото',
            'abv', 'og', 'ibu', 'ebc',  # Технические параметры пива
            'naличие', 'availability', 'stock', 'склад', 'остаток',  # Статус наличия
            'годен до', 'expiry', 'expires', 'срок годности',  # Сроки
            'скидки', 'акции', 'discount', 'promo',  # Промо
            'заказ', 'order', 'кол-во',  # Заказ/количество
            'стоимость', 'сумма',  # Дублирует цену
            'код', 'sku', 'артикул', 'id',  # Коды и артикулы
            'описание', 'description', 'комментарий',  # Описания
            'вид продукции', 'категория', 'category',  # Категории
            'unnamed',  # Безымянные колонки
            'abv / og / ibu',  # Комбинированная техническая колонка
        ]
        # Проверяем точное совпадение и вхождение
        if cleaned_lower in ignore_columns:
            return "IGNORE"
        if any(ignored in cleaned_lower for ignored in ['unnamed', 'остаток', 'заказ', 'сумма', 'код', 'срок', 'годн', 'abv', 'ibu', 'og', 'наличи']):
            return "IGNORE"
        
        # Использование ML-модели
        if self.model:
            try:
                prediction = self.model.predict([cleaned_name])[0]
                return prediction
            except Exception as e:
                print(f"Ошибка при предсказании: {e}")
                return self._fallback_detection(cleaned_name)
        else:
            return self._fallback_detection(cleaned_name)
    
    def _fallback_detection(self, column_name: str) -> str:
        """
        Резервный метод определения типа колонки по ключевым словам.
        
        Args:
            column_name: Название колонки
            
        Returns:
            str: Тип колонки
        """
        name_lower = column_name.lower()
        
        # PRICE - проверяем ПЕРВЫМ и ТОЧНО
        # Точное совпадение имеет приоритет
        if name_lower in ["цена", "price", "стоимость", "cost"]:
            return "PRICE"
        if any(word in name_lower for word in ["цена", "price", "стоимость", "cost", "руб", "₽", "rub"]):
            return "PRICE"
        
        # BREWERY
        if any(word in name_lower for word in ["пивоварня", "brewery", "производитель", "бренд", "brand"]):
            return "BREWERY"
        
        # NAME
        if any(word in name_lower for word in ["название", "наименование", "name", "пиво", "beer", "продукт", "product"]):
            return "NAME"
        
        # VOLUME - проверяем ПЕРЕД STYLE чтобы "тип тары" не считался стилем
        volume_keywords = ["объем", "объём", "volume", "литр", "мл", "ml", "упаковка"]
        if any(word in name_lower for word in volume_keywords):
            return "VOLUME"
        # "Тип тары" и "Тара" - это объем (ВАЖНО: до проверки STYLE!)
        if "тара" in name_lower:
            return "VOLUME"
        
        # STYLE (после VOLUME!)
        if any(word in name_lower for word in ["стиль", "style", "тип", "type", "сорт"]):
            return "STYLE"
        
        return "IGNORE"

