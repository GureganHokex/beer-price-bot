"""
Тесты для построителя заказов.
"""
import pytest
import json
from pathlib import Path
from core.order_builder import build_json, build_text_report, build_summary


class TestOrderBuilder:
    """Тесты для построителя заказов."""
    
    @pytest.fixture
    def sample_items(self):
        """Примеры позиций пива."""
        return [
            {
                "пивоварня": "AF Brew",
                "название": "Black Magic IPA",
                "стиль": "IPA",
                "объем": "0.5 л",
                "цена": "250 руб."
            },
            {
                "пивоварня": "Zagovor",
                "название": "Silence is Golden",
                "стиль": "Pale Ale",
                "объем": "0.33 л",
                "цена": "220 руб."
            },
        ]
    
    def test_build_json(self, sample_items, tmp_path):
        """Тест создания JSON файла."""
        output_path = tmp_path / "test_output.json"
        
        json_str = build_json(sample_items, str(output_path))
        
        # Проверка, что файл создан
        assert output_path.exists()
        
        # Проверка содержимого
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[0]["пивоварня"] == "AF Brew"
        assert data[1]["название"] == "Silence is Golden"
    
    def test_build_text_report(self, sample_items):
        """Тест создания текстового отчета."""
        report = build_text_report(sample_items)
        
        assert "Найдено позиций: 2" in report
        assert "Black Magic IPA" in report
        assert "AF Brew" in report
        assert "Pale Ale" in report
    
    def test_build_text_report_empty(self):
        """Тест отчета с пустыми данными."""
        report = build_text_report([])
        assert "Данные не найдены" in report
    
    def test_build_summary(self, sample_items):
        """Тест создания сводки."""
        summary = build_summary(sample_items)
        
        assert summary["total_items"] == 2
        assert "AF Brew" in summary["breweries"]
        assert "Zagovor" in summary["breweries"]
        assert "IPA" in summary["styles"]
        assert "Pale Ale" in summary["styles"]
    
    def test_build_summary_empty(self):
        """Тест сводки с пустыми данными."""
        summary = build_summary([])
        
        assert summary["total_items"] == 0
        assert len(summary["breweries"]) == 0
        assert len(summary["styles"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

