"""
Автоматическое дообучение ML-модели на новых данных.
"""
import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pandas as pd
import config


class AdaptiveColumnClassifier:
    """Классификатор с возможностью дообучения."""
    
    def __init__(self):
        """Инициализация."""
        self.model = None
        self.training_samples = []
        self.training_labels = []
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Загрузить существующую модель или создать новую."""
        if config.COLUMN_CLASSIFIER_PATH.exists():
            with open(config.COLUMN_CLASSIFIER_PATH, 'rb') as f:
                self.model = pickle.load(f)
        else:
            # Создаем базовую модель
            self.model = Pipeline([
                ('vectorizer', TfidfVectorizer(
                    analyzer='char',
                    ngram_range=(1, 3),
                    max_features=100
                )),
                ('classifier', MultinomialNB(alpha=0.1))
            ])
    
    def learn_from_dataframe(self, df: pd.DataFrame, column_mappings: dict):
        """
        Дообучить модель на новых данных из DataFrame.
        
        Args:
            df: DataFrame с данными
            column_mappings: Маппинг {имя_колонки: тип}
        """
        for col_name, col_type in column_mappings.items():
            self.training_samples.append(col_name)
            self.training_labels.append(col_type)
    
    def retrain_and_save(self):
        """Переобучить модель на накопленных данных и сохранить."""
        if len(self.training_samples) < 5:
            return  # Слишком мало данных
        
        # Обучаем модель
        self.model.fit(self.training_samples, self.training_labels)
        
        # Сохраняем
        config.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(config.COLUMN_CLASSIFIER_PATH, 'wb') as f:
            pickle.dump(self.model, f)
        
        print(f"✅ Модель переобучена на {len(self.training_samples)} примерах")

