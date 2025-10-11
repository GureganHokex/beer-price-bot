"""
Формирование выходных данных (JSON, CSV).
"""
import json
from typing import List, Dict
from pathlib import Path


def build_json(beer_items: List[Dict], output_path: str) -> str:
    """
    Сформировать JSON файл с данными.
    
    Args:
        beer_items: Список позиций пива
        output_path: Путь для сохранения
        
    Returns:
        str: JSON строка
    """
    json_data = json.dumps(beer_items, ensure_ascii=False, indent=2)
    
    # Сохранение в файл
    Path(output_path).write_text(json_data, encoding='utf-8')
    
    return json_data


def build_text_report(beer_items: List[Dict]) -> str:
    """
    Сформировать текстовый отчет с группировкой по названию пива.
    
    Args:
        beer_items: Список позиций пива
        
    Returns:
        str: Текстовый отчет
    """
    if not beer_items:
        return "Данные не найдены."
    
    # Группируем по названию пива (объединяем разные варианты тары)
    grouped = {}
    for item in beer_items:
        name = item.get('название', 'Без названия')
        if name not in grouped:
            grouped[name] = {
                'пивоварня': item.get('пивоварня'),
                'стиль': item.get('стиль'),
                'варианты': []
            }
        
        # Добавляем вариант тары (только уникальные)
        variant = {
            'объем': item.get('объем'),
            'цена': item.get('цена'),
            'остаток': item.get('остаток')
        }
        # Проверяем что такого варианта еще нет
        if variant not in grouped[name]['варианты']:
            grouped[name]['варианты'].append(variant)
    
    # Сортируем: сначала с кегами, потом остальные
    def sort_key(item):
        name, data = item
        has_keg = any('кег' in str(v.get('объем', '')).lower() for v in data['варианты'])
        return (0 if has_keg else 1, name)
    
    sorted_items = sorted(grouped.items(), key=sort_key)
    
    lines = [f"Найдено позиций: {len(sorted_items)}\n"]
    
    for idx, (name, data) in enumerate(sorted_items, 1):
        lines.append(f"{idx}. {name}")
        
        if data.get('пивоварня'):
            lines.append(f"   Пивоварня: {data['пивоварня']}")
        
        if data.get('стиль'):
            lines.append(f"   Стиль: {data['стиль']}")
        
        # Показываем все варианты тары
        if len(data['варианты']) == 1:
            # Один вариант
            v = data['варианты'][0]
            if v.get('объем'):
                lines.append(f"   Объем: {v['объем']}")
            if v.get('цена'):
                lines.append(f"   Цена: {v['цена']}")
            if v.get('остаток'):
                stock = v['остаток']
                # Если число - добавляем "шт", если текст - как есть
                if isinstance(stock, int):
                    lines.append(f"   Остаток: {stock} шт")
                else:
                    lines.append(f"   Наличие: {stock}")
        else:
            # Несколько вариантов тары
            lines.append(f"   Варианты:")
            for v in data['варианты']:
                volume = v.get('объем', '—')
                price = v.get('цена', '—')
                stock = v.get('остаток')
                if stock:
                    if isinstance(stock, int):
                        lines.append(f"     • {volume} — {price} (ост: {stock} шт)")
                    else:
                        lines.append(f"     • {volume} — {price} ({stock})")
                else:
                    lines.append(f"     • {volume} — {price}")
        
        lines.append("")
    
    return '\n'.join(lines)


def build_summary(beer_items: List[Dict]) -> Dict:
    """
    Сформировать сводку по данным.
    
    Args:
        beer_items: Список позиций пива
        
    Returns:
        Dict: Сводная информация
    """
    summary = {
        "total_items": len(beer_items),
        "breweries": set(),
        "styles": set(),
    }
    
    for item in beer_items:
        if item.get('пивоварня'):
            summary["breweries"].add(item['пивоварня'])
        if item.get('стиль'):
            summary["styles"].add(item['стиль'])
    
    summary["breweries"] = list(summary["breweries"])
    summary["styles"] = list(summary["styles"])
    
    return summary

