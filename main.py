"""
Основной модуль системы мониторинга недвижимости
"""

import argparse
import asyncio
import logging
from pathlib import Path
import json
from jinja2 import Environment, FileSystemLoader
from datetime import datetime


def get_monitor():
    """
    Фабричная функция для создания экземпляра RealEstateMonitor
    с ленивыми импортами для избежания циклических импортов.
    """
    from core.database import DatabaseManager
    from core.file_manager import FileOrganizer
    from core.backup_system import BackupManager
    from scraper.cian_parser import CianScraper
    from scraper.avito_parser import AvitoScraper
    from analytics.analyzer import RealEstateAnalyzer
    from utils.logger import setup_logger
    from config.settings import BASE_DIR, LOG_LEVEL

    class RealEstateMonitor:
        """
        Основной класс системы мониторинга недвижимости.
        """

        def __init__(self):
            self.logger = setup_logger(__name__, LOG_LEVEL)
            self.db = DatabaseManager()
            self.organizer = FileOrganizer()
            self.backup_manager = BackupManager()
            self.analyzer = RealEstateAnalyzer()

            # Инициализация скраперов
            self.scrapers = {
                'cian': CianScraper(),
                'avito': AvitoScraper()
            }

        async def scrape_data(self, sources: list, pages: int = 3) -> dict:
            """
            Сбор данных с указанных источников.
            """
            self.logger.info(f"Запуск сбора данных с {sources}")
            all_results = {}

            for source in sources:
                if source in self.scrapers:
                    try:
                        results = await self.scrapers[source].scrape(pages=pages)
                        all_results[source] = results
                        self.logger.info(f"Собрано {len(results)} объектов с {source}")
                    except Exception as e:
                        self.logger.error(f"Ошибка скрапинга {source}: {e}")

            return all_results

        def save_results_to_json(self, data: dict, filename="results.json"):
            """
            Сохранение результатов в JSON.
            """
            filepath = BASE_DIR / filename
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Результаты сохранены в {filepath.resolve()}")

        def save_results_to_db(self, data: dict):
            """
            Сохранение результатов в базу данных.
            """
            for source, properties in data.items():
                for prop in properties:
                    self.db.save_property(prop)
            self.logger.info("Результаты сохранены в базу данных")

        def generate_html_report(self, data: dict, report_path="reports/report.html"):
            """
            Генерация HTML-отчета.
            """
            env = Environment(loader=FileSystemLoader("templates"))
            template = env.get_template("report_template.html")

            rendered = template.render(
                properties=[prop for source in data.values() for prop in source],
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            path = Path(report_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
            self.logger.info(f"HTML-отчет сгенерирован: {path.resolve()}")

        def analyze_market(self, report_type: str = "quick") -> dict:
            """
            Анализ рыночных данных.
            """
            return self.analyzer.comprehensive_analysis(report_type)

        def organize_files(self, target_dir: Path = None) -> dict:
            """
            Организация файлов в проекте.
            """
            return self.organizer.organize_directory(target_dir or BASE_DIR)

        def create_backup(self, backup_type: str = "incremental") -> str:
            """
            Создание резервной копии.
            """
            return self.backup_manager.create_backup(backup_type)

    return RealEstateMonitor()


def main():
    """
    Главная функция для запуска системы мониторинга недвижимости.
    """
    parser = argparse.ArgumentParser(
        description="Система мониторинга недвижимости",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:
  python main.py scrape --sources cian avito --pages 5
  python main.py analyze --report-type full
  python main.py organize --path ./data
  python main.py backup --type full
  python main.py report --sources cian avito --pages 3
        '''
    )

    subparsers = parser.add_subparsers(dest="command", help="Команды")

    # Парсер для скрапинга
    scrape_parser = subparsers.add_parser("scrape", help="Сбор данных о недвижимости")
    scrape_parser.add_argument("--sources", nargs="+", choices=["cian", "avito"], default=["cian", "avito"],
                               help="Источники для сбора данных")
    scrape_parser.add_argument("--pages", type=int, default=3, help="Количество страниц для обработки")

    # Парсер для анализа
    analyze_parser = subparsers.add_parser("analyze", help="Анализ данных")
    analyze_parser.add_argument("--report-type", choices=["quick", "full", "trends"], default="quick",
                                help="Тип отчета")

    # Парсер для организации файлов
    organize_parser = subparsers.add_parser("organize", help="Организация файлов")
    organize_parser.add_argument("--path", type=Path, default=Path.cwd(), help="Путь для организации")

    # Парсер для бэкапа
    backup_parser = subparsers.add_parser("backup", help="Резервное копирование")
    backup_parser.add_argument("--type", choices=["full", "incremental", "differential"], default="incremental",
                               help="Тип бэкапа")

    # Парсер для генерации отчета
    report_parser = subparsers.add_parser("report", help="Генерация HTML-отчета")
    report_parser.add_argument("--sources", nargs="+", choices=["cian", "avito"], default=["cian", "avito"],
                               help="Источники для сбора данных")
    report_parser.add_argument("--pages", type=int, default=3, help="Количество страниц для обработки")

    args = parser.parse_args()

    monitor = get_monitor()

    if args.command == "scrape":
        print(f"🚀 Запуск сбора данных с {args.sources}...")
        results = asyncio.run(monitor.scrape_data(args.sources, args.pages))
        total_properties = sum(len(data) for data in results.values())
        print(f"✅ Собрано {total_properties} объектов недвижимости")

        # Сохраняем результаты
        monitor.save_results_to_json(results)
        monitor.save_results_to_db(results)

    elif args.command == "analyze":
        print("📊 Запуск анализа рынка недвижимости...")
        report = monitor.analyze_market(args.report_type)
        print(f"✅ Отчет сгенерирован: {report.get('report_path', 'N/A')}")

    elif args.command == "organize":
        print("🗂️ Организация файлов...")
        result = monitor.organize_files(args.path)
        print(f"✅ Организовано {result.get('files_moved', 0)} файлов")

    elif args.command == "backup":
        print("💾 Создание резервной копии...")
        backup_path = monitor.create_backup(args.type)
        print(f"✅ Бэкап создан: {backup_path}")

    elif args.command == "report":
        print("🎨 Генерация HTML-отчета...")
        results = asyncio.run(monitor.scrape_data(args.sources, args.pages))
        monitor.generate_html_report(results)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
