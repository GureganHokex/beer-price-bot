"""
Конфигурация приложения.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Database
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./beer_orders.db")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PROJECTS_DIR = DATA_DIR / "projects"
ML_MODELS_DIR = BASE_DIR / "ml" / "models"
TEMP_DIR = BASE_DIR / "temp_files"

# Создание директорий
for directory in [DATA_DIR, UPLOADS_DIR, PROJECTS_DIR, ML_MODELS_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ML Model
COLUMN_CLASSIFIER_PATH = ML_MODELS_DIR / "column_classifier.pkl"
VECTORIZER_PATH = ML_MODELS_DIR / "vectorizer.pkl"

# Beer styles keywords
BEER_STYLES = [
    "IPA", "NEIPA", "DIPA", "Imperial IPA", "Session IPA",
    "Lager", "Pilsner", "Pils",
    "Stout", "Imperial Stout", "Milk Stout", "Oatmeal Stout",
    "Porter", "Baltic Porter",
    "Ale", "Pale Ale", "APA", "Amber Ale", "Red Ale",
    "Wheat", "Weizen", "Witbier", "Hefeweizen",
    "Sour", "Gose", "Berliner Weisse",
    "Saison", "Farmhouse",
    "Barleywine",
    "Scotch Ale",
    "Brown Ale",
]

