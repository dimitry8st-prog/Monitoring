"""
Парсер для сбора данных с Циан
"""

import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional
import logging

from playwright.async_api import async_playwright

from config.settings import SCRAPING_CONFIG


class CianScraper:
    """Скрапер для сайта cian.ru"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://www.cian.ru"
        self.config = SCRAPING_CONFIG

    async def scrape(self, pages: int = 3, property_type: str = "flat") -> List[Dict]:
        """Основной метод скрапинга"""
        properties = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.config['user_agent']
                )
                page = await context.new_page()

                for page_num in range(1, pages + 1):
                    self.logger.info(f"Обработка страницы {page_num}")
                    url = self._build_url(property_type, page_num)

                    try:
                        await page.goto(url, timeout=self.config['timeout'] * 1000)
                        await page.wait_for_selector('[data-name="CardComponent"]', timeout=10000)

                        page_properties = await self._parse_page(page)
                        properties.extend(page_properties)
                        self.logger.info(f"Страница {page_num}: собрано {len(page_properties)} объектов")

                        await asyncio.sleep(self.config['request_delay'])
                    except Exception as e:
                        self.logger.error(f"Ошибка на странице {page_num}: {e}")
                        break  # Прерываем цикл при ошибке

                await browser.close()
        except Exception as e:
            self.logger.error(f"Критическая ошибка скрапинга: {e}")

        self.logger.info(f"Скрапинг завершен. Всего собрано: {len(properties)} объектов")
        return properties

    def _build_url(self, property_type: str, page: int) -> str:
        """Построение URL для поиска"""
        base_params = {
            "flat": "cat.php?deal_type=rent&engine_version=2&offer_type=flat",
            "apartment": "cat.php?deal_type=rent&engine_version=2&offer_type=apartment",
            "room": "cat.php?deal_type=rent&engine_version=2&offer_type=room"
        }
        param = base_params.get(property_type, base_params['flat'])
        return f"{self.base_url}/{param}&p={page}"

    async def _parse_page(self, page) -> List[Dict]:
        """Парсинг страницы с объявлениями"""
        properties = []
        cards = await page.query_selector_all('[data-name="CardComponent"]')

        for card in cards:
            try:
                property_data = await self._parse_property_card(card)
                if property_data and self._validate_property_data(property_data):
                    properties.append(property_data)
            except Exception as e:
                self.logger.debug(f"Ошибка парсинга карточки: {e}")
                continue

        return properties

    async def _parse_property_card(self, card) -> Optional[Dict]:
        """Парсинг отдельной карточки объявления"""
        try:
            title_elem = await card.query_selector('[data-name="TitleComponent"]')
            price_elem = await card.query_selector('[data-mark="MainPrice"]')
            address_elem = await card.query_selector('[data-name="GeoLabel"]')
            link_elem = await card.query_selector('a[href*="/rent/"]')

            if not all([title_elem, price_elem, address_elem, link_elem]):
                return None

            title = (await title_elem.text_content()).strip()
            price_text = await price_elem.text_content()
            address = (await address_elem.text_content()).strip()
            url = await link_elem.get_attribute('href')

            price = self._parse_price(price_text)
            if not price:
                return None

            details = await self._parse_property_details(card)

            return {
                'external_id': self._extract_external_id(url),
                'title': title,
                'price': price,
                'price_per_sqm': details.get('price_per_sqm'),
                'location': address,
                'district': self._extract_district(address),
                'area': details.get('area'),
                'rooms': details.get('rooms'),
                'floor': details.get('floor'),
                'total_floors': details.get('total_floors'),
                'property_type': self._determine_property_type(title, details),
                'source': 'cian',
                'url': f"{self.base_url}{url}" if url.startswith('/') else url,
                'description': details.get('description', ''),
                'scraped_at': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.debug(f"Ошибка парсинга карточки: {e}")
            return None

    def _parse_price(self, price_text: str) -> Optional[float]:
        """Парсинг цены из текста"""
        if not price_text:
            return None

        clean_text = re.sub(r'[^\d.]', '', price_text)
        try:
            return float(clean_text) if clean_text else None
        except ValueError:
            return None

    def _extract_district(self, address: str) -> str:
        """Извлечение района из адреса"""
        if not address:
            return ''

        parts = address.split(',')
        return parts[1].strip() if len(parts) > 1 else ''

    def _extract_external_id(self, url: str) -> str:
        """Извлечение внешнего ID из URL"""
        match = re.search(r'/(\d+)/?$', url)
        return f"cian_{match.group(1)}" if match else f"cian_{hash(url)}"

    def _determine_property_type(self, title: str, details: Dict) -> str:
        """Определение типа недвижимости"""
        title_lower = title.lower() if title else ''

        if 'комната' in title_lower or details.get('rooms') == 1:
            return 'room'
        elif 'апартаменты' in title_lower:
            return 'apartment'
        else:
            return 'flat'

    def _validate_property_data(self, data: Dict) -> bool:
        """Валидация данных объекта"""
        required_fields = ['title', 'price', 'location', 'url']
        return all(data.get(field) for field in required_fields)

    async def _parse_property_details(self, card) -> Dict:
        """Парсинг дополнительных деталей объекта"""
        details = {}

        try:
            # Ищем элементы с дополнительной информацией
            details_elem = await card.query_selector('[data-name="GeneralInfoSectionRowComponent"]')
            if details_elem:
                details_text = await details_elem.text_content()

                # Парсим площадь
                area_match = re.search(r'(\d+\.?\d*)\s*м²', details_text)
                if area_match:
                    details['area'] = float(area_match.group(1))

                # Парсим этажность
                floor_match = re.search(r'(\d+)\s*/\s*(\d+)\s*этаж', details_text)
                if floor_match:
                    details['floor'] = int(floor_match.group(1))
                    details['total_floors'] = int(floor_match.group(2))

                # Парсим количество комнат
                rooms_match = re.search(r'(\d+)\s*комн', details_text)
                if rooms_match:
                    details['rooms'] = int(rooms_match.group(1))

            # Ищем цену за квадратный метр
            price_per_sqm_elem = await card.query_selector('[data-name="PricePerSquareMeter"]')
            if price_per_sqm_elem:
                price_per_sqm_text = await price_per_sqm_elem.text_content()
                clean_text = re.sub(r'[^\d.]', '', price_per_sqm_text)
                details['price_per_sqm'] = float(clean_text) if clean_text else None

            # Ищем описание
            description_elem = await card.query_selector('[data-name="Description"]')
            if description_elem:
                details['description'] = (await description_elem.text_content()).strip()

        except Exception as e:
            self.logger.debug(f"Ошибка парсинга деталей: {e}")

        return details


# """
# Парсер для сбора данных с Циан
# """
#
# import asyncio
# import re
# from datetime import datetime
# from typing import Dict, List, Optional
# import logging
#
# from playwright.async_api import async_playwright
#
# from config.settings import SCRAPING_CONFIG
#
#
# class CianScraper:
#     """Скрапер для сайта cian.ru"""
#
#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
#         self.base_url = "https://www.cian.ru"
#         self.config = SCRAPING_CONFIG
#
#     async def scrape(self, pages: int = 3, property_type: str = "flat") -> List[Dict]:
#         """Основной метод скрапинга"""
#         self.logger.info(f"Запуск скрапинга Циан: {pages} страниц, тип: {property_type}")
#
#         properties = []
#
#         async with async_playwright() as p:
#             browser = await p.chromium.launch(headless=True)
#             context = await browser.new_context(
#                 user_agent=self.config['user_agent']
#             )
#             page = await context.new_page()
#
#             try:
#                 for page_num in range(1, pages + 1):
#                     self.logger.info(f"Обработка страницы {page_num}")
#
#                     url = self._build_url(property_type, page_num)
#                     await page.goto(url, timeout=self.config['timeout'] * 1000)
#
#                     # Ждем загрузки контента
#                     await page.wait_for_selector('[data-name="CardComponent"]', timeout=10000)
#
#                     # Собираем данные с текущей страницы
#                     page_properties = await self._parse_page(page)
#                     properties.extend(page_properties)
#
#                     self.logger.info(f"Страница {page_num}: собрано {len(page_properties)} объектов")
#
#                     # Задержка между запросами
#                     await asyncio.sleep(self.config['request_delay'])
#
#             except Exception as e:
#                 self.logger.error(f"Ошибка скрапинга: {e}")
#             finally:
#                 await browser.close()
#
#         self.logger.info(f"Скрапинг завершен. Всего собрано: {len(properties)} объектов")
#         return properties
#
#     def _build_url(self, property_type: str, page: int) -> str:
#         """Построение URL для поиска"""
#         base_params = {
#             "flat": "cat.php?deal_type=rent&engine_version=2&offer_type=flat",
#             "apartment": "cat.php?deal_type=rent&engine_version=2&offer_type=flat",
#             "room": "cat.php?deal_type=rent&engine_version=2&offer_type=room"
#         }
#
#         # url_template = f"{self.base_url}/{base_params.get(property_type, base_params['flat']}&p=
#         # {page}
#         # "
#         url_template = f"{self.base_url}/{base_params.get(property_type, base_params['flat'])}&p="
#         return url_template
#
#     async def _parse_page(self, page) -> List[Dict]:
#         """Парсинг страницы с объявлениями"""
#         properties = []
#
#         # Находим все карточки объявлений
#         cards = await page.query_selector_all('[data-name="CardComponent"]')
#
#         for card in cards:
#             try:
#                 property_data = await self._parse_property_card(card)
#                 if property_data and self._validate_property_data(property_data):
#                     properties.append(property_data)
#
#             except Exception as e:
#                 self.logger.debug(f"Ошибка парсинга карточки: {e}")
#                 continue
#
#         return properties
#
#     async def _parse_property_card(self, card) -> Optional[Dict]:
#         """Парсинг отдельной карточки объявления"""
#         try:
#             # Извлекаем основные данные
#             title_elem = await card.query_selector('[data-name="TitleComponent"]')
#             price_elem = await card.query_selector('[data-mark="MainPrice"]')
#             address_elem = await card.query_selector('[data-name="GeoLabel"]')
#             link_elem = await card.query_selector('a[href*="/rent/"]')
#
#             if not all([title_elem, price_elem, address_elem, link_elem]):
#                 return None
#
#             title = await title_elem.text_content()
#             price_text = await price_elem.text_content()
#             address = await address_elem.text_content()
#             url = await link_elem.get_attribute('href')
#
#             # Парсим цену
#             price = self._parse_price(price_text)
#             if not price:
#                 return None
#
#             # Парсим дополнительные параметры
#             details = await self._parse_property_details(card)
#
#             property_data = {
#                 'external_id': self._extract_external_id(url),
#                 'title': title.strip() if title else '',
#                 'price': price,
#                 'price_per_sqm': details.get('price_per_sqm'),
#                 'location': address.strip() if address else '',
#                 'district': self._extract_district(address),
#                 'area': details.get('area'),
#                 'rooms': details.get('rooms'),
#                 'floor': details.get('floor'),
#                 'total_floors': details.get('total_floors'),
#                 'property_type': self._determine_property_type(title, details),
#                 'source': 'cian',
#                 'url': f"{self.base_url}{url}" if url.startswith('/') else url,
#                 'description': details.get('description', ''),
#                 'scraped_at': datetime.now().isoformat()
#             }
#
#             return property_data
#
#         except Exception as e:
#             self.logger.debug(f"Ошибка парсинга карточки: {e}")
#             return None
#
#     def _parse_price(self, price_text: str) -> Optional[float]:
#         """Парсинг цены из текста"""
#         if not price_text:
#             return None
#
#         # Удаляем все нецифровые символы кроме точки
#         clean_text = re.sub(r'[^\d.]', '', price_text)
#         try:
#             return float(clean_text) if clean_text else None
#         except ValueError:
#             return None
#
#     def _extract_district(self, address: str) -> str:
#         """Извлечение района из адреса"""
#         if not address:
#             return ''
#
#         # Простая логика извлечения района
#         parts = address.split(',')
#         return parts[1].strip() if len(parts) > 1 else ''
#
#     def _extract_external_id(self, url: str) -> str:
#         """Извлечение внешнего ID из URL"""
#         match = re.search(r'/(\d+)/?$', url)
#         return f"cian_{match.group(1)}" if match else f"cian_{hash(url)}"
#
#     def _determine_property_type(self, title: str, details: Dict) -> str:
#         """Определение типа недвижимости"""
#         title_lower = title.lower() if title else ''
#
#         if 'комната' in title_lower or details.get('rooms') == 1:
#             return 'room'
#         elif 'апартаменты' in title_lower:
#             return 'apartment'
#         else:
#             return 'flat'
#
#     def _validate_property_data(self, data: Dict) -> bool:
#         """Валидация данных объекта"""
#         required_fields = ['title', 'price', 'location', 'url']
#         return all(data.get(field) for field in required_fields)