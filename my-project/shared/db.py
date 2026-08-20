"""
Shared Database utilities for all projects
"""

import sqlite3
import os
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    """Simple SQLite database wrapper"""

    def __init__(self, db_path: str = "data/project.db"):
        self.db_path = db_path
        # Создать папку если её нет
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Возвращать как словари
        return conn

    def execute(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            return results
        finally:
            conn.close()

    def execute_insert(
        self, query: str, params: tuple = ()
    ) -> int:
        """Execute INSERT query and return last row id"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute UPDATE/DELETE query and return affected rows"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def create_table(self, query: str) -> None:
        """Create table if not exists"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
        finally:
            conn.close()

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """
        result = self.execute(query, (table_name,))
        return len(result) > 0


# Пример использования:
# db = Database("data/hh.db")
# results = db.execute("SELECT * FROM vacancies WHERE salary > ?", (100000,))
