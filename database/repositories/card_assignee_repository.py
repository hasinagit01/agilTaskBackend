import sqlite3
from typing import Dict, List
from ..connection import get_connection
from ..exceptions import DuplicateError


class CardAssigneeRepository:
    def add(self, card_id: int, user_id: int) -> None:
        with get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO card_assignees (card_id, user_id) VALUES (?, ?)",
                    (card_id, user_id),
                )
            except sqlite3.IntegrityError as e:
                raise DuplicateError(str(e)) from e

    def remove(self, card_id: int, user_id: int) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM card_assignees WHERE card_id = ? AND user_id = ?",
                (card_id, user_id),
            )
            return cursor.rowcount

    def find_by_card(self, card_id: int) -> List[Dict]:
        query = """
            SELECT u.id AS user_id, u.email
            FROM users u
            JOIN card_assignees ca ON u.id = ca.user_id
            WHERE ca.card_id = ?
            ORDER BY u.id ASC
        """
        with get_connection() as conn:
            rows = conn.execute(query, (card_id,)).fetchall()
            return [dict(row) for row in rows]
