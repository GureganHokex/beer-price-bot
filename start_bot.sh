#!/bin/bash

# Скрипт для запуска бота

echo "Активация виртуального окружения..."
source venv/bin/activate

echo "Проверка наличия ML-модели..."
if [ ! -f "ml/models/column_classifier.pkl" ]; then
    echo "ML-модель не найдена. Обучение модели..."
    python ml/train_detector.py
fi

echo "Запуск бота..."
python run_bot.py

