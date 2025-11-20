"""
Модуль для работы с базой данных недвижимости
"""

import sqlite3
from pathlib import Path
from config.settings import DATABASE_URL
from utils.logger import setup_logger

# Логгер для модуля
logger = setup_logger(__name__)


class DatabaseManager:
    """
    Менеджер базы данных для работы с объектами недвижимости.
    """

    def __init__(self):
        """
        Инициализация менеджера базы данных.
        """
        self.connection = self.connect_to_db(DATABASE_URL)
        self.create_tables()

    def connect_to_db(self, db_url):
        """
        Подключение к базе данных.
        """
        try:
            # Извлекаем путь к файлу из URL
            db_path = db_url.replace("sqlite:///", "")
            logger.info(f"Подключение к базе данных: {db_path}")
            connection = sqlite3.connect(db_path)
            return connection
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise

    def create_tables(self):
        """
        Создание таблиц, если они не существуют.
        """
        try:
            with self.connection:
                self.connection.execute("""
                    CREATE TABLE IF NOT EXISTS properties (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source TEXT NOT NULL,
                        title TEXT NOT NULL,
                        price REAL,
                        location TEXT,
                        url TEXT UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("Таблица 'properties' создана или уже существует")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise

    def save_property(self, property_data):
        """
        Сохранение объекта недвижимости в базу данных.
        """
        try:
            with self.connection:
                self.connection.execute("""
                    INSERT OR IGNORE INTO properties (source, title, price, location, url)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    property_data.get("source"),
                    property_data.get("title"),
                    property_data.get("price"),
                    property_data.get("location"),
                    property_data.get("url")
                ))
                logger.info(f"Сохранён объект недвижимости: {property_data.get('title')}")
        except sqlite3.IntegrityError:
            logger.warning(f"Объект уже существует в базе данных: {property_data.get('url')}")
        except Exception as e:
            logger.error(f"Ошибка сохранения объекта недвижимости: {e}")

    def get_all_properties(self):
        """
        Получение всех объектов недвижимости из базы данных.
        """
        try:
            with self.connection:
                cursor = self.connection.execute("""
                    SELECT * FROM properties ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения данных из базы: {e}")
            return []

    def update_property(self, property_id, updates):
        """
        Обновление данных объекта недвижимости.
        """
        try:
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [property_id]
            with self.connection:
                self.connection.execute(f"""
                    UPDATE properties
                    SET {set_clause}
                    WHERE id = ?
                """, values)
                logger.info(f"Обновлен объект недвижимости с ID: {property_id}")
        except Exception as e:
            logger.error(f"Ошибка обновления объекта недвижимости: {e}")

    def delete_property(self, property_id):
        """
        Удаление объекта недвижимости по ID.
        """
        try:
            with self.connection:
                self.connection.execute("""
                    DELETE FROM properties
                    WHERE id = ?
                """, (property_id,))
                logger.info(f"Удален объект недвижимости с ID: {property_id}")
        except Exception as e:
            logger.error(f"Ошибка удаления объекта недвижимости: {e}")

    def close(self):
        """
        Закрытие соединения с базой данных.
        """
        try:
            if self.connection:
                self.connection.close()
                logger.info("Соединение с базой данных закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения: {e}")

    def __del__(self):
        """
        Автоматическое закрытие соединения при удалении объекта.
        """
        self.close()

# import sqlite3
# from datetime import datetime
# from typing import Dict, List, Any
# import logging
#
# from config.settings import DATABASE_CONFIG
#
#
# class DatabaseManager:
#     """Менеджер базы данных для хранения информации о недвижимости"""
#
#     def __init__(self):
#         self.db_path = DATABASE_CONFIG['path']
#         self.logger = logging.getLogger(__name__)
#         self._init_database()
#
#     def _init_database(self):
#         """Инициализация таблиц базы данных"""
#         with self._get_connection() as conn:
#             # Таблица свойств недвижимости
#             conn.execute('''
#                 CREATE TABLE IF NOT EXISTS properties (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     external_id TEXT UNIQUE,
#                     title TEXT NOT NULL,
#                     price DECIMAL(12,2),
#                     price_per_sqm DECIMAL(8,2),
#                     location TEXT,
#                     district TEXT,
#                     area DECIMAL(6,2),
#                     rooms INTEGER,
#                     floor INTEGER,
#                     total_floors INTEGER,
#                     property_type TEXT,
#                     source TEXT,
#                     url TEXT UNIQUE,
#                     description TEXT,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     scraped_at TIMESTAMP,
#                     is_active BOOLEAN DEFAULT TRUE,
#                     latitude REAL,
#                     longitude REAL
#                 )
#             ''')
#
#             # Таблица истории цен
#             conn.execute('''
#                 CREATE TABLE IF NOT EXISTS price_history (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     property_id INTEGER,
#                     price DECIMAL(12,2),
#                     recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     FOREIGN KEY (property_id) REFERENCES properties (id)
#                 )
#             ''')
#
#             # Таблица рыночной статистики
#             conn.execute('''
#                 CREATE TABLE IF NOT EXISTS market_stats (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     district TEXT,
#                     property_type TEXT,
#                     avg_price DECIMAL(8,2),
#                     avg_price_per_sqm DECIMAL(8,2),
#                     properties_count INTEGER,
#                     calculation_date DATE,
#                     UNIQUE(district, property_type, calculation_date)
#                 )
#             ''')
#
#             # Индексы для улучшения производительности
#             conn.execute('CREATE INDEX IF NOT EXISTS idx_properties_location ON properties(location)')
#             conn.execute('CREATE INDEX IF NOT EXISTS idx_properties_price ON properties(price)')
#             conn.execute('CREATE INDEX IF NOT EXISTS idx_properties_type ON properties(property_type)')
#             conn.execute('CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(recorded_at)')
#
#     def _get_connection(self) -> sqlite3.Connection:
#         """Получение соединения с базой данных"""
#         return sqlite3.connect(
#             self.db_path,
#             timeout=DATABASE_CONFIG['timeout'],
#             detect_types=DATABASE_CONFIG['detect_types']
#         )
#
#     def save_property(self, property_data: Dict[str, Any]) -> bool:
#         """Сохранение/обновление данных о недвижимости"""
#         try:
#             with self._get_connection() as conn:
#                 cursor = conn.cursor()
#
#                 # Проверяем существование записи
#                 cursor.execute(
#                     'SELECT id FROM properties WHERE external_id = ? OR url = ?',
#                     (property_data.get('external_id'), property_data.get('url'))
#                 )
#                 existing = cursor.fetchone()
#
#                 if existing:
#                     # Обновление существующей записи
#                     query = '''
#                         UPDATE properties SET
#                         title=?, price=?, price_per_sqm=?, location=?, district=?,
#                         area=?, rooms=?, floor=?, total_floors=?, property_type=?,
#                         description=?, scraped_at=?, is_active=TRUE
#                         WHERE id=?
#                     '''
#                     params = (
#                         property_data['title'],
#                         property_data['price'],
#                         property_data.get('price_per_sqm'),
#                         property_data['location'],
#                         property_data.get('district'),
#                         property_data.get('area'),
#                         property_data.get('rooms'),
#                         property_data.get('floor'),
#                         property_data.get('total_floors'),
#                         property_data.get('property_type'),
#                         property_data.get('description'),
#                         datetime.now(),
#                         existing[0]
#                     )
#                 else:
#                     # Вставка новой записи
#                     query = '''
#                         INSERT INTO properties (
#                             external_id, title, price, price_per_sqm, location, district,
#                             area, rooms, floor, total_floors, property_type, source, url,
#                             description, scraped_at, latitude, longitude
#                         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                     '''
#                     params = (
#                         property_data.get('external_id'),
#                         property_data['title'],
#                         property_data['price'],
#                         property_data.get('price_per_sqm'),
#                         property_data['location'],
#                         property_data.get('district'),
#                         property_data.get('area'),
#                         property_data.get('rooms'),
#                         property_data.get('floor'),
#                         property_data.get('total_floors'),
#                         property_data.get('property_type'),
#                         property_data.get('source'),
#                         property_data.get('url'),
#                         property_data.get('description'),
#                         datetime.now(),
#                         property_data.get('latitude'),
#                         property_data.get('longitude')
#                     )
#
#                 cursor.execute(query, params)
#
#                 # Сохраняем в историю цен
#                 if existing and property_data['price']:
#                     cursor.execute(
#                         'INSERT INTO price_history (property_id, price) VALUES (?, ?)',
#                         (existing[0] if existing else cursor.lastrowid, property_data['price'])
#                     )
#
#                 conn.commit()
#                 self.logger.debug(f"Сохранен объект: {property_data['title']}")
#                 return True
#
#         except Exception as e:
#             self.logger.error(f"Ошибка сохранения объекта: {e}")
#             return False
#
#     def get_properties(self, filters: Dict = None, limit: int = 100) -> List[Dict]:
#         """Получение объектов недвижимости с фильтрами"""
#         try:
#             with self._get_connection() as conn:
#                 conn.row_factory = sqlite3.Row
#                 cursor = conn.cursor()
#
#                 query = '''
#                     SELECT * FROM properties
#                     WHERE is_active = TRUE
#                 '''
#                 params = []
#
#                 if filters:
#                     conditions = []
#                     for key, value in filters.items():
#                         if key == 'min_price':
#                             conditions.append('price >= ?')
#                             params.append(value)
#                         elif key == 'max_price':
#                             conditions.append('price <= ?')
#                             params.append(value)
#                         elif key == 'district':
#                             conditions.append('district = ?')
#                             params.append(value)
#                         elif key == 'property_type':
#                             conditions.append('property_type = ?')
#                             params.append(value)
#                         elif key == 'min_rooms':
#                             conditions.append('rooms >= ?')
#                             params.append(value)
#
#                     if conditions:
#                         query += ' AND ' + ' AND '.join(conditions)
#
#                 query += ' ORDER BY created_at DESC LIMIT ?'
#                 params.append(limit)
#
#                 cursor.execute(query, params)
#                 return [dict(row) for row in cursor.fetchall()]
#
#         except Exception as e:
#             self.logger.error(f"Ошибка получения объектов: {e}")
#             return []
#
#     def get_market_stats(self, district: str = None) -> Dict[str, Any]:
#         """Получение рыночной статистики"""
#         try:
#             with self._get_connection() as conn:
#                 cursor = conn.cursor()
#
#                 query = '''
#                     SELECT
#                         COUNT(*) as total_properties,
#                         AVG(price) as avg_price,
#                         AVG(price_per_sqm) as avg_price_sqm,
#                         MIN(price) as min_price,
#                         MAX(price) as max_price,
#                         property_type,
#                         COUNT(*) as type_count
#                     FROM properties
#                     WHERE is_active = TRUE
#                 '''
#                 params = []
#
#                 if district:
#                     query += ' AND district = ?'
#                     params.append(district)
#
#                 query += ' GROUP BY property_type'
#
#                 cursor.execute(query, params)
#                 results = cursor.fetchall()
#
#                 stats = {
#                     'total_properties': 0,
#                     'avg_price': 0,
#                     'avg_price_sqm': 0,
#                     'by_type': {}
#                 }
#
#                 for row in results:
#                     stats['total_properties'] += row[0]
#                     stats['by_type'][row[5]] = {
#                         'count': row[6],
#                         'avg_price': row[1],
#                         'avg_price_sqm': row[2]
#                     }
#
#                 if results:
#                     stats['avg_price'] = sum(row[1] or 0 for row in results) / len(results)
#                     stats['avg_price_sqm'] = sum(row[2] or 0 for row in results) / len(results)
#
#                 return stats
#
#         except Exception as e:
#             self.logger.error(f"Ошибка получения статистики: {e}")
#             return {}
# class DatabaseManager:
#     pass
