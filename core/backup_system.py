import os
import shutil
import datetime
from pathlib import Path

class BackupManager:
    """Менеджер резервного копирования"""

    def __init__(self):
        self.backup_dir = Path("../backups")
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, backup_type: str = 'incremental') -> str:
        """
        Создаёт резервную копию проекта.

        :param backup_type: Тип бэкапа ('full', 'incremental', 'differential')
        :return: Путь к созданной резервной копии
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}_{backup_type}"
        backup_path = self.backup_dir / backup_name

        try:
            if backup_type == 'full':
                # Полная копия всех данных
                shutil.copytree("../data", backup_path / "data", dirs_exist_ok=True)
                shutil.copytree("../reports", backup_path / "reports", dirs_exist_ok=True)
            else:
                # Инкрементальная — только новые/изменённые файлы (упрощённо)
                data_dir = Path("../data")
                if data_dir.exists():
                    for item in data_dir.iterdir():
                        if item.is_file():
                            dest = backup_path / "data" / item.name
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, dest)

            return str(backup_path.resolve())

        except Exception as e:
            print(f"❌ Ошибка создания бэкапа: {e}")
            return ""