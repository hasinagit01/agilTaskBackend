import sqlite3
from abc import ABC
from typing import Dict, List, Optional
from ..connection import get_connection
from ..exceptions import DuplicateError

class BaseRepository(ABC):
    """Repository de base avec méthodes communes."""
    
    def __init__(self, table_name: str):
        if not table_name.replace("_", "").isalnum():
            raise ValueError(f"Nom de table invalide : {table_name!r}")
        self.table_name = table_name
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Exécute une requête SELECT et retourne les résultats."""
        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    def execute_command(self, query: str, params: tuple = ()) -> int:
        """Exécute une commande (INSERT, UPDATE, DELETE) et retourne le nombre de lignes affectées."""
        with get_connection() as conn:
            try:
                cursor = conn.execute(query, params)
            except sqlite3.IntegrityError as e:
                raise DuplicateError(str(e)) from e
            return cursor.rowcount

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Exécute un INSERT et retourne l'ID généré."""
        with get_connection() as conn:
            try:
                cursor = conn.execute(query, params)
            except sqlite3.IntegrityError as e:
                raise DuplicateError(str(e)) from e
            return cursor.lastrowid
    
    def count(self, filters: Optional[dict] = None) -> int:
        if filters:
            conditions = " AND ".join(f"{col} = ?" for col in filters.keys())
            query = f"SELECT COUNT(*) as total FROM {self.table_name} WHERE {conditions}"
            rows = self.execute_query(query, tuple(filters.values()))
        else:
            query = f"SELECT COUNT(*) as total FROM {self.table_name}"
            rows = self.execute_query(query)
        return rows[0]["total"] if rows else 0

    def find_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        if limit is None:
            query = f"SELECT * FROM {self.table_name} ORDER BY id DESC"
            return self.execute_query(query)
        query = f"SELECT * FROM {self.table_name} ORDER BY id DESC LIMIT ? OFFSET ?"
        return self.execute_query(query, (limit, offset))
    
    def insert(self, data: dict) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        return self.execute_insert(query, tuple(data.values()))

    def update_by_id(self, id_value: int, data: dict) -> int:
        set_clause = ", ".join(f"{col} = ?" for col in data.keys())
        query = f"UPDATE {self.table_name} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        return self.execute_command(query, (*data.values(), id_value))

    def find_by(self, filters: dict, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        conditions = " AND ".join(f"{col} = ?" for col in filters.keys())
        if limit is None:
            query = f"SELECT * FROM {self.table_name} WHERE {conditions} ORDER BY id DESC"
            return self.execute_query(query, tuple(filters.values()))
        query = f"SELECT * FROM {self.table_name} WHERE {conditions} ORDER BY id DESC LIMIT ? OFFSET ?"
        return self.execute_query(query, (*filters.values(), limit, offset))

    def delete_by_ids(self, ids: List[int]) -> int:
        placeholders = ", ".join("?" * len(ids))
        query = f"DELETE FROM {self.table_name} WHERE id IN ({placeholders})"
        return self.execute_command(query, tuple(ids))