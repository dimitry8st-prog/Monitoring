from typing import List, Dict

class AvitoScraper:
    """Заглушка для парсера Avito"""

    def __init__(self):
        self.base_url = "https://www.avito.ru"

    async def scrape(self, pages: int = 3) -> List[Dict]:
        """
        Заглушка: возвращает тестовые данные.
        В реальном проекте здесь будет логика парсинга Avito.
        """
        print(f"✅ AvitoScraper: имитация сбора данных с {pages} страниц")
        return [
            {
                "title": f"Тестовое объявление {i}",
                "price": f"{i * 1000} руб.",
                "url": f"https://avito.ru/test{i}"
            }
            for i in range(1, pages + 1)
        ]