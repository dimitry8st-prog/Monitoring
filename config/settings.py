"""
Настройки проекта мониторинга недвижимости
"""

from pathlib import Path
import os

# === Базовые пути ===
BASE_DIR = Path(__file__).parent.parent  # Корневая директория проекта
DATA_DIR = BASE_DIR / 'data'             # Директория для данных
REPORTS_DIR = BASE_DIR / 'reports'       # Директория для отчётов
LOGS_DIR = BASE_DIR / 'logs'             # Директория для логов
BACKUP_DIR = BASE_DIR / 'backups'        # Директория для бэкапов

# Создание необходимых директорий
DIRECTORIES = [DATA_DIR, REPORTS_DIR, LOGS_DIR, BACKUP_DIR]
for directory in DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)

# === Настройки базы данных ===
DATABASE_CONFIG = {
    'path': DATA_DIR / 'real_estate.db',  # Путь к файлу базы данных
    'timeout': 30,                        # Таймаут подключения (в секундах)
    'detect_types': 1                     # Автоматическое определение типов данных
}

DATABASE_URL = "sqlite:///data/real_estate.db"

# === Настройки логирования ===
LOG_LEVEL = 'INFO'                        # Уровень логирования
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_SIZE = 10 * 1024 * 1024           # Максимальный размер лог-файла (10MB)
LOG_BACKUP_COUNT = 5                      # Количество ротаций логов

# === Настройки скрапинга ===
SCRAPING_CONFIG = {
    'request_delay': 2,                   # Задержка между запросами (в секундах)
    'timeout': 30,                        # Таймаут запроса (в секундах)
    'max_retries': 3,                     # Максимальное количество попыток при ошибках
    'user_agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/119.0.0.0 Safari/537.36'
    )                                     # User-Agent для HTTP-запросов
}

# === Настройки анализа ===
ANALYSIS_CONFIG = {
    'price_outlier_threshold': 3,         # Порог для выявления выбросов цен (в стандартных отклонениях)
    'min_data_points': 10,                # Минимальное количество точек данных для анализа
    'trend_period_days': 30               # Период для анализа трендов (в днях)
}

# === Настройки бэкапа ===
BACKUP_CONFIG = {
    'keep_days': 7,                       # Сколько дней хранить бэкапы
    'compression': True,                  # Использовать сжатие (True/False)
    'monitor_paths': ['data', 'src', 'reports', 'config']  # Директории для бэкапа
}