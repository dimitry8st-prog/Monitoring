"""
Настройка системы логирования для проекта
"""

import logging
import logging.handlers
from pathlib import Path

from config.settings import LOGS_DIR, LOG_LEVEL, LOG_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT


def setup_logger(name: str, level: str = LOG_LEVEL) -> logging.Logger:
    """Настройка логгера для модуля"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(getattr(logging, level.upper()))

        # Форматтер
        formatter = logging.Formatter(LOG_FORMAT)

        # File handler с ротацией
        log_file = LOGS_DIR / f"{name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=LOG_MAX_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Добавляем обработчики
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def get_scraper_logger():
    """Специальный логгер для скрапинга"""
    return setup_logger('scraper')


def get_analysis_logger():
    """Специальный логгер для анализа"""
    return setup_logger('analysis')


def get_database_logger():
    """Специальный логгер для базы данных"""
    return setup_logger('database')