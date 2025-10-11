"""
Генерация тестовых Excel файлов с прайс-листами.
"""
import pandas as pd
from pathlib import Path

# Создание директории для тестовых данных
test_data_dir = Path(__file__).parent / "test_data"
test_data_dir.mkdir(exist_ok=True)


def generate_afbrew_pricelist():
    """Генерация прайс-листа AF Brew."""
    data = {
        "Название пива": [
            "Black Magic IPA",
            "Hoppy Lager",
            "Stout Imperial",
            "Pale Ale Session",
        ],
        "Стиль": ["IPA", "Lager", "Stout", "Pale Ale"],
        "Объем": ["0.5 л", "0.33 л", "0.5 л", "0.33 л"],
        "Цена (руб)": [250, 180, 280, 200],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_data_dir / "afbrew_pricelist.xlsx", index=False)
    print(f"Создан: afbrew_pricelist.xlsx")


def generate_zagovor_pricelist():
    """Генерация прайс-листа Zagovor."""
    data = {
        "Продукт": [
            "Silence is Golden",
            "Dark Side IPA",
            "Witbier Classic",
        ],
        "Тип": ["Pale Ale", "IPA", "Witbier"],
        "Тара": ["0.5 л", "0.5 л", "0.33 л"],
        "Стоимость": ["220", "260", "190"],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_data_dir / "zagovor_pricelist.xlsx", index=False)
    print(f"Создан: zagovor_pricelist.xlsx")


def generate_kegs_pricelist():
    """Генерация прайс-листа с кегами."""
    data = {
        "Пивоварня": ["Craft Republic", "Craft Republic", "BrewDog"],
        "Наименование": ["Mosaic IPA", "Red Ale", "Punk IPA"],
        "Объём": ["30 л (кега)", "30 л (кега)", "50 л (кега)"],
        "Цена": [5500, 4800, 9000],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_data_dir / "kegs_supplier.xlsx", index=False)
    print(f"Создан: kegs_supplier.xlsx")


def generate_baltica_pricelist():
    """Генерация прайс-листа Балтика."""
    data = {
        "Название": ["Балтика 3", "Балтика 7", "Балтика 9"],
        "Описание": ["Классическое", "Экспортное", "Крепкое"],
        "Литраж": ["0.5", "0.5", "0.5"],
        "Руб.": [45, 55, 60],
        "Артикул": ["BAL-003", "BAL-007", "BAL-009"],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_data_dir / "балтика_прайс.xlsx", index=False)
    print(f"Создан: балтика_прайс.xlsx")


def generate_mixed_format():
    """Генерация прайс-листа со смешанным форматом."""
    data = {
        "Beer Name": [
            "BrewDog Punk IPA 0.33л",
            "Zagovor Witbier (0.5L)",
            "Лаборатория Stout 500мл",
        ],
        "Price RUB": [280, 240, 310],
        "Comment": ["Импорт", "Локальное", "Крафт"],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_data_dir / "поставщик_А_октябрь.xlsx", index=False)
    print(f"Создан: поставщик_А_октябрь.xlsx")


def generate_craft_republic():
    """Генерация прайс-листа Craft Republic 2024."""
    data = {
        "Brewery": ["Craft Republic"] * 4,
        "Name": ["Mosaic IPA", "Session Pale Ale", "Imperial Stout", "Pilsner"],
        "Style": ["IPA", "Pale Ale", "Stout", "Pilsner"],
        "Volume (L)": [0.5, 0.33, 0.5, 0.33],
        "Price": [320, 210, 380, 190],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_data_dir / "craft_republic_2024.xlsx", index=False)
    df.to_csv(test_data_dir / "craft_republic_2024.csv", index=False)
    print(f"Создан: craft_republic_2024.xlsx и .csv")


if __name__ == "__main__":
    print("Генерация тестовых Excel файлов...")
    generate_afbrew_pricelist()
    generate_zagovor_pricelist()
    generate_kegs_pricelist()
    generate_baltica_pricelist()
    generate_mixed_format()
    generate_craft_republic()
    print("\nВсе тестовые файлы созданы!")

