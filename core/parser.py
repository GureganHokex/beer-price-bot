"""
Парсер Excel файлов с прайс-листами пива.
"""
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
from core.column_detector import ColumnDetector
from core.filters import (
    extract_beer_style,
    extract_brewery_from_filename,
    extract_volume,
    extract_price,
    clean_text
)


class ExcelParser:
    """Парсер Excel файлов с данными о пиве."""
    
    def __init__(self, auto_learn: bool = True):
        """
        Инициализация парсера.
        
        Args:
            auto_learn: Автоматически обучаться на новых таблицах
        """
        self.detector = ColumnDetector()
        self.auto_learn = auto_learn
        self.learned_columns = []  # Для накопления обучающих данных
    
    def parse_file(self, file_path: str, brewery_override: Optional[str] = None) -> List[Dict]:
        """
        Парсинг Excel файла (все листы).
        
        Args:
            file_path: Путь к Excel файлу
            brewery_override: Переопределить пивоварню (если None, извлекается из имени файла)
            
        Returns:
            List[Dict]: Список позиций пива
        """
        path = Path(file_path)
        
        # Определение пивоварни
        brewery = brewery_override or extract_brewery_from_filename(path.name)
        
        # Получаем все листы
        all_beer_items = []
        
        try:
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            print(f"Обработка {len(sheet_names)} листов...")
            
            for sheet_name in sheet_names:
                # Читаем каждый лист
                df = self._read_excel_with_header_detection(file_path, sheet_name=sheet_name)
                
                if df is None or df.empty:
                    continue
                
                # Классификация колонок
                column_types = self._classify_columns(df)
                
                # Автоматическое обучение на новых данных
                if self.auto_learn:
                    self._learn_from_columns(column_types)
                
                # Извлечение данных
                beer_items = self._extract_beer_items(df, column_types, brewery)
                all_beer_items.extend(beer_items)
                
                print(f"  • {sheet_name}: {len(beer_items)} позиций")
        
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {e}")
            return []
        
        return all_beer_items
    
    def _learn_from_columns(self, column_types: Dict[str, str]):
        """
        Накопить данные для обучения из классифицированных колонок.
        
        Args:
            column_types: Классифицированные колонки
        """
        for col_name, col_type in column_types.items():
            if col_type != "IGNORE":
                self.learned_columns.append((col_name, col_type))
    
    def save_learned_data(self):
        """
        Сохранить накопленные данные и переобучить модель.
        """
        if not self.learned_columns or len(self.learned_columns) < 3:
            return
        
        from ml.vectorizer import AdaptiveColumnClassifier
        
        adaptive = AdaptiveColumnClassifier()
        for col_name, col_type in self.learned_columns:
            adaptive.training_samples.append(col_name)
            adaptive.training_labels.append(col_type)
        
        adaptive.retrain_and_save()
        
        # Перезагружаем детектор
        self.detector._load_model()
    
    def _read_excel_with_header_detection(self, file_path: str, sheet_name=0) -> Optional[pd.DataFrame]:
        """
        Прочитать Excel с автоматическим определением строки заголовков.
        
        Args:
            file_path: Путь к файлу
            sheet_name: Номер или название листа (по умолчанию 0)
            
        Returns:
            Optional[pd.DataFrame]: DataFrame или None
        """
        # Сначала читаем без заголовков
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        if df_raw.empty:
            return None
        
        # Ищем строку с заголовками (содержит ключевые слова)
        header_keywords = [
            'название', 'наименование', 'name', 'пиво', 'beer', 'product',
            'цена', 'price', 'стоимость', 'cost',
            'объем', 'объём', 'volume', 'тара',
            'стиль', 'style', 'тип', 'type'
        ]
        
        header_row = None
        for idx, row in df_raw.iterrows():
            # Считаем сколько ключевых слов найдено в строке
            row_text = ' '.join([str(cell).lower() for cell in row if pd.notna(cell)])
            matches = sum(1 for keyword in header_keywords if keyword in row_text)
            
            # Если найдено 2+ ключевых слова - это заголовки
            if matches >= 2:
                header_row = idx
                break
        
        # Если нашли заголовки - читаем с них
        if header_row is not None:
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
            # Пропускаем пустые строки после заголовков
            df = df.dropna(how='all')
            # Очищаем имена колонок от пробелов
            df.columns = [str(col).strip() for col in df.columns]
            return df
        else:
            # Если не нашли - читаем как обычно
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            df.columns = [str(col).strip() for col in df.columns]
            return df
    
    def _classify_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Классифицировать колонки DataFrame.
        
        Args:
            df: DataFrame для анализа
            
        Returns:
            Dict[str, str]: Маппинг {название_колонки: тип}
        """
        column_types = {}
        
        for col in df.columns:
            col_type = self.detector.detect_column_type(str(col))
            column_types[col] = col_type
        
        return column_types
    
    def _extract_beer_items(
        self,
        df: pd.DataFrame,
        column_types: Dict[str, str],
        brewery: Optional[str]
    ) -> List[Dict]:
        """
        Извлечь позиции пива из DataFrame.
        
        Args:
            df: DataFrame с данными
            column_types: Типы колонок
            brewery: Название пивоварни
            
        Returns:
            List[Dict]: Список позиций пива
        """
        beer_items = []
        
        # Найти колонки по типам
        name_cols = [col for col, typ in column_types.items() if typ == "NAME"]
        brewery_cols = [col for col, typ in column_types.items() if typ == "BREWERY"]
        
        # Для стиля: приоритет колонке с точным названием "Стиль" или "Style"
        style_cols = [col for col, typ in column_types.items() if typ == "STYLE"]
        exact_style_cols = [col for col in style_cols if col.lower() in ['стиль', 'style']]
        if exact_style_cols:
            style_cols = exact_style_cols
        
        volume_cols = [col for col, typ in column_types.items() if typ == "VOLUME"]
        
        # Для цены: приоритет колонке с названием "ЦЕНА" или "Price"
        price_cols = [col for col, typ in column_types.items() if typ == "PRICE"]
        # Ищем точное совпадение "ЦЕНА" или "Price"
        exact_price_cols = [col for col in price_cols if col.lower() in ['цена', 'price', 'стоимость']]
        if exact_price_cols:
            price_cols = exact_price_cols  # Используем только точные совпадения
        
        # Для объема: игнорируем колонку "заказ" - там количество, а не объем
        volume_cols = [col for col in volume_cols if 'заказ' not in col.lower() and 'order' not in col.lower()]
        
        # Обработка каждой строки
        last_beer_name = None  # Для подхвата названия для кег в следующих строках
        
        for idx, row in df.iterrows():
            # Пропускаем пустые строки
            if row.isna().all():
                continue
            
            # Извлечение данных
            item = {
                "пивоварня": brewery,
                "название": None,
                "стиль": None,
                "объем": None,
                "цена": None,
                "остаток": None,
            }
            
            # Название
            if name_cols:
                for col in name_cols:
                    val = row[col]
                    if pd.notna(val):
                        item["название"] = clean_text(val)
                        last_beer_name = item["название"]  # Запоминаем для следующих строк
                        break
            
            # Если название пустое - возможно это альтернативная тара (кега) для предыдущего пива
            if not item["название"] and last_beer_name:
                # Проверяем есть ли объем с кегой
                volume_text = None
                if volume_cols:
                    for col in volume_cols:
                        val = row[col]
                        if pd.notna(val):
                            volume_text = str(val).strip()
                            break
                
                # Если это кега - используем название из предыдущей строки
                if volume_text and ('кег' in volume_text.lower() or 'keg' in volume_text.lower()):
                    item["название"] = last_beer_name
            
            # Пивоварня (если есть в колонках, переопределяет название из файла)
            if brewery_cols:
                for col in brewery_cols:
                    val = row[col]
                    if pd.notna(val):
                        item["пивоварня"] = clean_text(val)
                        break
            
            # Стиль
            if style_cols:
                for col in style_cols:
                    val = row[col]
                    if pd.notna(val):
                        style = clean_text(val)
                        item["стиль"] = style
                        break
            
            # Если стиль не найден, пробуем извлечь из названия
            if not item["стиль"] and item["название"]:
                extracted_style = extract_beer_style(item["название"])
                if extracted_style:
                    item["стиль"] = extracted_style
            
            # Объем (НЕ используем clean_text - он обрезает многострочный текст)
            volume_text = None
            if volume_cols:
                for col in volume_cols:
                    val = row[col]
                    if pd.notna(val):
                        # Для объемов сохраняем весь текст
                        volume_text = str(val).strip()
                        item["объем"] = extract_volume(volume_text) or volume_text
                        break
            
            # Если объем не найден, пробуем извлечь из названия
            if not item["объем"] and item["название"]:
                item["объем"] = extract_volume(item["название"])
            
            # Цена
            if price_cols:
                for col in price_cols:
                    val = row[col]
                    if pd.notna(val):
                        price_text = clean_text(val)
                        item["цена"] = extract_price(price_text, item["объем"])
                        break
            
            # Остаток / Наличие (в штуках или текстом: "много", "мало", "достаточно")
            stock_cols = [col for col in df.columns if 'остаток' in col.lower() or 'остатк' in col.lower() or 'наличие' in col.lower() or 'наличи' in col.lower()]
            if stock_cols:
                for col in stock_cols:
                    val = row[col]
                    if pd.notna(val):
                        val_str = str(val).strip().lower()
                        # Пробуем преобразовать в число
                        try:
                            item["остаток"] = int(float(val))
                        except (ValueError, TypeError):
                            # Если не число - сохраняем текст
                            item["остаток"] = val_str
                        break
            
            # Фильтрация: добавляем только валидные позиции пива
            if self._is_valid_beer_item(item):
                beer_items.append(item)
        
        return beer_items
    
    def _is_valid_beer_item(self, item: Dict) -> bool:
        """
        Проверить, является ли позиция валидным товаром (пиво/сидр/комбуча/напиток).
        
        Args:
            item: Позиция для проверки
            
        Returns:
            bool: True если валидная позиция
        """
        name = item.get("название", "")
        price = item.get("цена", "")
        stock = item.get("остаток")
        volume = item.get("объем", "")
        
        # Должно быть название
        if not name or len(name) < 2:
            return False
        
        # Проверяем это кега или нет
        is_keg = 'кег' in str(volume).lower()
        
        # Фильтр по остаткам (НЕ применяется к кегам!)
        if stock is not None and not is_keg:
            # Если это число - фильтруем по количеству >= 10 (только для банок/бутылок)
            if isinstance(stock, int):
                if stock < 10:
                    return False
            # Если текст - оставляем "много", "мало", "достаточно", игнорируем "скидка", "новинка"
            elif isinstance(stock, str):
                # Игнорируем не связанные с наличием метки
                if stock in ['скидка', 'новинка', 'акция']:
                    pass  # Не фильтруем
                # Для малого остатка можно добавить фильтрацию, пока оставляем всё
        
        name_lower = name.lower()
        
        # Игнорируем ТОЛЬКО явный мусор (заголовки разделов, примечания, категории)
        ignore_keywords = [
            "уважаемые партнеры",
            "внимание",
            "примечание",
            "этикетка",
            "честный знак",
            "введением",
            "отгрузка",
            "упаковке",
            "кратно упаковке",
            "two peaks brew lab",
            "сидры incider",
            "otherlab",
            "платиновая коллекция",
            "специальные сорта и коллаб",
            "бокалы и мерч",
            "крафт фасовка",
            "крафт розлив",
            "классическое розлив",
            "классическое фасовка",
        ]
        
        # Проверяем на служебные записи
        if any(keyword in name_lower for keyword in ignore_keywords):
            return False
        
        # Игнорируем короткие служебные слова (статусы)
        short_ignore = ["много", "мало", "нет в наличии", "достаточно", "н/д", "нет", "ё", ""]
        if name_lower.strip() in short_ignore:
            return False
        
        # Игнорируем строки из 1 символа
        if len(name.strip()) <= 1:
            return False
        
        # Игнорируем очень длинные тексты (>200 символов - это описания/примечания)
        if len(name) > 200:
            return False
        
        # ГЛАВНОЕ ПРАВИЛО: если есть название + цена = это товар!
        # Не фильтруем по заглавным - названия пива могут быть заглавными
        has_valid_price = price and any(char.isdigit() for char in str(price))
        has_valid_name = len(name.strip()) >= 2
        
        return has_valid_name and has_valid_price

