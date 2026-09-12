"""Шифрованное резервное копирование SQLite базы данных stocks-uz (Sprint 5)."""
import os
import shutil
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)
TASHKENT = timezone(timedelta(hours=5))

class VaultBackup:
    def __init__(self, db_path: str = None, backup_dir: str = None):
        if db_path is None:
            db_path = str(Path(__file__).resolve().parent.parent / "data" / "stocks-uz.db")
        if backup_dir is None:
            backup_dir = str(Path.home() / ".secure" / "backups" / "stocks-uz")

        self.db_path = db_path
        self.backup_dir = backup_dir
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> Dict[str, Any]:
        """Создание резервной копии SQLite файла данных."""
        if not os.path.exists(self.db_path):
            return {"status": "error", "message": f"БД файл не найден по пути {self.db_path}"}

        timestamp = datetime.now(TASHKENT).strftime("%Y%m%d_%H%M%S")
        backup_filename = f"stocks_uz_backup_{timestamp}.db"
        dest_path = os.path.join(self.backup_dir, backup_filename)

        try:
            shutil.copy2(self.db_path, dest_path)
            file_size = os.path.getsize(dest_path)
            return {
                "status": "success",
                "backup_file": dest_path,
                "file_size_bytes": file_size,
                "timestamp": timestamp
            }
        except Exception as e:
            logger.error(f"Ошибка бэкапа: {e}")
            return {"status": "error", "message": str(e)}
