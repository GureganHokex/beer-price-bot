"""
Обучение ML-модели для классификации колонок Excel.
"""
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import config


# Обучающие данные: примеры заголовков колонок
TRAINING_DATA = [
    # BREWERY
    ("Пивоварня", "BREWERY"),
    ("Brewery", "BREWERY"),
    ("Производитель", "BREWERY"),
    ("Бренд", "BREWERY"),
    ("Brand", "BREWERY"),
    ("Завод", "BREWERY"),
    
    # NAME
    ("Название", "NAME"),
    ("Наименование", "NAME"),
    ("Пиво", "NAME"),
    ("Name", "NAME"),
    ("Beer", "NAME"),
    ("Product", "NAME"),
    ("Товар", "NAME"),
    ("Продукт", "NAME"),
    ("Позиция", "NAME"),
    
    # STYLE
    ("Стиль", "STYLE"),
    ("Style", "STYLE"),
    ("Тип", "STYLE"),
    ("Type", "STYLE"),
    ("Сорт", "STYLE"),
    
    # VOLUME
    ("Объем", "VOLUME"),
    ("Объём", "VOLUME"),
    ("Volume", "VOLUME"),
    ("Емкость", "VOLUME"),
    ("Ёмкость", "VOLUME"),
    ("Литраж", "VOLUME"),
    ("л", "VOLUME"),
    ("L", "VOLUME"),
    ("мл", "VOLUME"),
    ("ml", "VOLUME"),
    ("Тара", "VOLUME"),
    ("Упаковка", "VOLUME"),
    
    # PRICE
    ("Цена", "PRICE"),
    ("Price", "PRICE"),
    ("Стоимость", "PRICE"),
    ("Cost", "PRICE"),
    ("Руб", "PRICE"),
    ("₽", "PRICE"),
    ("RUB", "PRICE"),
    ("Рублей", "PRICE"),
    
    # IGNORE
    ("Артикул", "IGNORE"),
    ("SKU", "IGNORE"),
    ("Код", "IGNORE"),
    ("ID", "IGNORE"),
    ("Примечание", "IGNORE"),
    ("Комментарий", "IGNORE"),
    ("Comment", "IGNORE"),
    ("Описание", "IGNORE"),
    ("Description", "IGNORE"),
    ("Картинка", "IGNORE"),
    ("Image", "IGNORE"),
    ("Фото", "IGNORE"),
    ("", "IGNORE"),
]


def train_column_classifier():
    """
    Обучить классификатор колонок и сохранить модель.
    
    Returns:
        Pipeline: Обученная модель
    """
    texts, labels = zip(*TRAINING_DATA)
    
    # Создание pipeline с векторизатором и классификатором
    model = Pipeline([
        ('vectorizer', TfidfVectorizer(
            analyzer='char',
            ngram_range=(1, 3),
            max_features=100
        )),
        ('classifier', MultinomialNB(alpha=0.1))
    ])
    
    # Обучение
    model.fit(texts, labels)
    
    # Сохранение модели
    config.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(config.COLUMN_CLASSIFIER_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Модель сохранена в {config.COLUMN_CLASSIFIER_PATH}")
    
    # Тестирование
    test_samples = [
        "Название пива",
        "Brewery Name",
        "Цена за литр",
        "Volume (L)",
        "Стиль пива",
        "Артикул"
    ]
    
    predictions = model.predict(test_samples)
    print("\nТестовые предсказания:")
    for sample, prediction in zip(test_samples, predictions):
        print(f"  '{sample}' -> {prediction}")
    
    return model


if __name__ == "__main__":
    train_column_classifier()

