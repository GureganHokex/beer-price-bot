#!/bin/bash

# Скрипт установки проекта

echo "=== Установка Beer Price Analyzer Bot ==="

# Создание виртуального окружения
echo "1. Создание виртуального окружения..."
python3 -m venv venv

# Активация виртуального окружения
echo "2. Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "3. Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
if [ ! -f ".env" ]; then
    echo "4. Создание .env файла..."
    cp .env.example .env
    echo "ВАЖНО: Отредактируйте .env и добавьте ваш TELEGRAM_BOT_TOKEN"
else
    echo "4. Файл .env уже существует"
fi

# Обучение ML-модели
echo "5. Обучение ML-модели..."
python ml/train_detector.py

# Генерация тестовых данных
echo "6. Генерация тестовых данных..."
python tests/generate_test_data.py

echo ""
echo "=== Установка завершена ==="
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте .env и добавьте ваш TELEGRAM_BOT_TOKEN"
echo "2. Запустите бота: ./start_bot.sh или python run_bot.py"
echo ""

