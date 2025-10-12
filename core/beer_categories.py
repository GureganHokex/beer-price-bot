"""
Категории и группировка стилей пива.
"""

# Категории стилей пива для формирования заказа
BEER_CATEGORIES = {
    "Лагеры (фильтрованное)": [
        "Lager", "Pilsner", "Pils", "Kölsch", "Kolsch", "Kellerbier",
        "Helles", "Dunkel", "Märzen", "Marzen", "Bock", "Doppelbock",
        "Maibock", "Eisbock", "Schwarzbier", "Vienna Lager"
    ],
    
    "Эли (нефильтрованное)": [
        "Ale", "Pale Ale", "IPA", "Imperial IPA", "DIPA", "TIPA",
        "Session IPA", "West Coast IPA", "East Coast IPA", "New England IPA", "NEIPA",
        "Hazy IPA", "Milkshake IPA", "Brut IPA"
    ],
    
    "Пшеничное": [
        "Weizen", "Weissbier", "Wheat", "Wheat Ale", "Hefeweizen",
        "Dunkelweizen", "Weizenbock", "Kristallweizen", "Berliner Weisse",
        "Witbier", "White Ale"
    ],
    
    "Темное": [
        "Stout", "Porter", "Imperial Stout", "Russian Imperial Stout", "RIS",
        "Milk Stout", "Sweet Stout", "Oatmeal Stout", "Coffee Stout",
        "Chocolate Stout", "Baltic Porter", "Smoked Porter"
    ],
    
    "Sour (кислое)": [
        "Sour", "Fruit Sour", "Kettle Sour", "Berliner Weisse"
    ],
    
    "Gose": [
        "Gose"
    ],
    
    "Lambic и фламандское": [
        "Lambic", "Gueuze", "Flanders Red", "Oud Bruin"
    ],
    
    "Бельгийское": [
        "Belgian Ale", "Dubbel", "Tripel", "Quadrupel", "Quad",
        "Saison", "Farmhouse Ale", "Belgian Strong Ale",
        "Belgian Pale Ale", "Witbier"
    ],
    
    "Сидр и медовуха": [
        "Cider", "Mead", "Сидр", "Медовуха", "Braggot"
    ],
    
    "Безалкогольное": [
        "Non-Alcoholic", "Безалкогольное", "БА", "0.0%", "Low Alcohol"
    ],
    
    "Специальное": [
        "Barleywine", "Scotch Ale", "Wee Heavy", "Old Ale",
        "English Bitter", "ESB", "Brown Ale", "Red Ale", "Amber Ale",
        "Cream Ale", "California Common", "Steam Beer"
    ]
}


def get_category_for_style(style: str) -> str:
    """
    Определить категорию для заданного стиля.
    
    Args:
        style: Стиль пива
        
    Returns:
        str: Название категории или "Другое"
    """
    if not style:
        return "Другое"
    
    style_lower = style.lower()
    
    for category, styles in BEER_CATEGORIES.items():
        for s in styles:
            if s.lower() in style_lower or style_lower in s.lower():
                return category
    
    return "Другое"


def get_categories_list() -> list:
    """
    Получить список всех категорий.
    
    Returns:
        list: Список названий категорий
    """
    return list(BEER_CATEGORIES.keys()) + ["Другое"]

