from typing import Dict, List, Optional
from ..connection import get_connection
from ..exceptions import DuplicateError
import sqlite3


class BoardMemberRepository:
    TABLE = "board_members"

    def add(self, board_id: int, user_id: int, role: str) -> None:
        query = f"INSERT INTO {self.TABLE} (board_id, user_id, role) VALUES (?, ?, ?)"
        with get_connection() as conn:
            try:
                conn.execute(query, (board_id, user_id, role))
            except sqlite3.IntegrityError as e:
                raise DuplicateError(str(e)) from e

    def find_role(self, board_id: int, user_id: int) -> Optional[str]:
        query = f"SELECT role FROM {self.TABLE} WHERE board_id = ? AND user_id = ?"
        with get_connection() as conn:
            row = conn.execute(query, (board_id, user_id)).fetchone()
        return row["role"] if row else None

    def update_role(self, board_id: int, user_id: int, role: str) -> int:
        query = f"UPDATE {self.TABLE} SET role = ? WHERE board_id = ? AND user_id = ?"
        with get_connection() as conn:
            cursor = conn.execute(query, (role, board_id, user_id))
            return cursor.rowcount

    def remove(self, board_id: int, user_id: int) -> int:
        query = f"DELETE FROM {self.TABLE} WHERE board_id = ? AND user_id = ?"
        with get_connection() as conn:
            cursor = conn.execute(query, (board_id, user_id))
            return cursor.rowcount

    def find_by_board(self, board_id: int) -> List[Dict]:
        query = f"""
            SELECT bm.board_id, bm.user_id, bm.role, bm.created_at, u.email
            FROM {self.TABLE} bm
            JOIN users u ON u.id = bm.user_id
            WHERE bm.board_id = ?
            ORDER BY bm.created_at ASC
        """
        with get_connection() as conn:
            rows = conn.execute(query, (board_id,)).fetchall()
        return [dict(row) for row in rows]
