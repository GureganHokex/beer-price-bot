"""
Тесты для парсера Excel файлов.
"""
import pytest
from pathlib import Path
from core.parser import ExcelParser
from core.filters import (
    extract_beer_style,
    extract_brewery_from_filename,
    extract_volume,
    extract_price
)


class TestFilters:
    """Тесты для фильтров."""
    
    def test_extract_beer_style(self):
        """Тест извлечения стиля пива."""
        assert extract_beer_style("Black Magic IPA") == "IPA"
        assert extract_beer_style("Imperial Stout Dark") == "Imperial Stout"
        assert extract_beer_style("Классическое Pilsner") == "Pilsner"
        assert extract_beer_style("Обычное пиво") is None
    
    def test_extract_brewery_from_filename(self):
        """Тест извлечения пивоварни из имени файла."""
        assert extract_brewery_from_filename("afbrew_pricelist.xlsx") is not None
        assert extract_brewery_from_filename("zagovor_price_2024.xlsx") is not None
        assert extract_brewery_from_filename("прайс_балтика.xlsx") is not None
    
    def test_extract_volume(self):
        """Тест извлечения объема."""
        assert extract_volume("0.5 л") == "0.5 л"
        assert extract_volume("500 мл") == "0.5 л"
        assert extract_volume("30 л кега") == "30 л (кега)"
        assert extract_volume("0.33L") == "0.33 л"
    
    def test_extract_price(self):
        """Тест извлечения цены."""
        assert extract_price("250") == "250 руб."
        assert extract_price("320 руб") == "320 руб."
        assert extract_price("5500", "30 л (кега)") is not None


class TestParser:
    """Тесты для парсера."""
    
    @pytest.fixture
    def parser(self):
        """Создание экземпляра парсера."""
        return ExcelParser()
    
    @pytest.fixture
    def test_data_dir(self):
        """Путь к тестовым данным."""
        return Path(__file__).parent / "test_data"
    
    def test_parser_initialization(self, parser):
        """Тест инициализации парсера."""
        assert parser is not None
        assert parser.detector is not None
    
    def test_parse_afbrew_file(self, parser, test_data_dir):
        """Тест парсинга файла AF Brew."""
        file_path = test_data_dir / "afbrew_pricelist.xlsx"
        
        if not file_path.exists():
            pytest.skip("Тестовый файл не найден. Запустите generate_test_data.py")
        
        items = parser.parse_file(str(file_path))
        
        assert len(items) > 0
        assert any("IPA" in str(item.get('название', '')) for item in items)
    
    def test_parse_kegs_file(self, parser, test_data_dir):
        """Тест парсинга файла с кегами."""
        file_path = test_data_dir / "kegs_supplier.xlsx"
        
        if not file_path.exists():
            pytest.skip("Тестовый файл не найден. Запустите generate_test_data.py")
        
        items = parser.parse_file(str(file_path))
        
        assert len(items) > 0
        # Проверка наличия кег
        assert any("кег" in str(item.get('объем', '')).lower() for item in items)
    
    def test_parse_with_brewery_override(self, parser, test_data_dir):
        """Тест парсинга с переопределением пивоварни."""
        file_path = test_data_dir / "craft_republic_2024.xlsx"
        
        if not file_path.exists():
            pytest.skip("Тестовый файл не найден")
        
        items = parser.parse_file(str(file_path), brewery_override="Test Brewery")
        
        if items:
            # Если пивоварня есть в файле, она переопределит brewery_override
            # Иначе будет использован override
            assert items[0].get('пивоварня') in ["Test Brewery", "Craft Republic"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

