"""
Модуль для организации и управления файлами проекта
"""

import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

from config.settings import BASE_DIR


class FileOrganizer:
    """Организатор файлов проекта недвижимости"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Категории файлов для недвижимости
        self.categories = {
            'Data': ['.csv', '.json', '.xlsx', '.xls', '.db', '.sqlite', '.parquet'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'Contracts': ['.pdf', '.doc', '.docx'],  # специально для договоров
            'Reports': ['.md', '.html', '.pdf'],
            'Code': ['.py', '.js', '.html', '.css', '.json', '.yaml', '.yml'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Backups': ['.bak', '.backup'],
            'Other': []
        }

    def organize_directory(self, target_dir: Path = None) -> Dict:
        """Организация файлов в директории"""
        if target_dir is None:
            target_dir = BASE_DIR

        self.logger.info(f"Организация файлов в {target_dir}")

        # Создание папок категорий
        for category in self.categories.keys():
            (target_dir / category).mkdir(exist_ok=True)

        files_moved = 0
        report = {
            'timestamp': datetime.now().isoformat(),
            'directory': str(target_dir),
            'files_moved': 0,
            'details': [],
            'errors': []
        }

        for file_path in target_dir.iterdir():
            if file_path.is_file() and self._should_organize(file_path):
                try:
                    category = self._get_file_category(file_path)
                    new_path = self._move_file(file_path, target_dir / category)

                    if new_path:
                        files_moved += 1
                        report['details'].append({
                            'original': file_path.name,
                            'new_location': str(new_path.relative_to(target_dir)),
                            'category': category
                        })

                except Exception as e:
                    report['errors'].append({
                        'file': file_path.name,
                        'error': str(e)
                    })
                    self.logger.error(f"Ошибка организации {file_path}: {e}")

        report['files_moved'] = files_moved

        # Сохранение отчета
        self._save_organization_report(target_dir, report)
        self.logger.info(f"Организация завершена. Перемещено {files_moved} файлов")

        return report

    def _should_organize(self, file_path: Path) -> bool:
        """Проверка, нужно ли организовывать файл"""
        ignore_files = {
            'organization_report.json',
            '.gitkeep',
            '.DS_Store'
        }

        return (file_path.name not in ignore_files and
                not file_path.name.startswith('.'))

    def _get_file_category(self, file_path: Path) -> str:
        """Определение категории файла"""
        extension = file_path.suffix.lower()

        for category, extensions in self.categories.items():
            if extension in extensions:
                return category

        return 'Other'

    def _move_file(self, file_path: Path, category_dir: Path) -> Optional[Path]:
        """Перемещение файла в категорию"""
        new_path = category_dir / file_path.name

        # Обработка конфликта имен
        counter = 1
        original_new_path = new_path
        while new_path.exists():
            stem = original_new_path.stem
            suffix = original_new_path.suffix
            new_path = category_dir / f"{stem}_{counter:02d}{suffix}"
            counter += 1

        shutil.move(str(file_path), str(new_path))
        self.logger.debug(f"Перемещен: {file_path.name} -> {category_dir.name}/")

        return new_path

    def _save_organization_report(self, target_dir: Path, report: Dict):
        """Сохранение отчета об организации"""
        report_path = target_dir / 'organization_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def find_files_by_pattern(self, pattern: str, search_dir: Path = None) -> List[Path]:
        """Поиск файлов по шаблону"""
        if search_dir is None:
            search_dir = BASE_DIR

        return list(search_dir.rglob(pattern))

    def cleanup_temp_files(self, temp_dir: Path = None) -> int:
        """Очистка временных файлов"""
        if temp_dir is None:
            temp_dir = BASE_DIR / 'temp'

        if not temp_dir.exists():
            return 0

        deleted_count = 0
        for temp_file in temp_dir.rglob('*'):
            if temp_file.is_file():
                try:
                    temp_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.logger.error(f"Ошибка удаления {temp_file}: {e}")

        self.logger.info(f"Удалено временных файлов: {deleted_count}")
        return deleted_count