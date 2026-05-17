import sqlite3
from typing import Dict, List
from .base import BaseRepository
from ..connection import get_connection
from ..exceptions import DuplicateError


class LabelRepository(BaseRepository):
    def __init__(self):
        super().__init__("labels")

    def create(self, board_id: int, name: str, color: str) -> int:
        return self.insert({"board_id": board_id, "name": name, "color": color})

    def update(self, label_id: int, name: str, color: str) -> int:
        return self.update_by_id(label_id, {"name": name, "color": color})

    def find_by_board(self, board_id: int) -> List[Dict]:
        query = f"SELECT * FROM {self.table_name} WHERE board_id = ? ORDER BY id ASC"
        return self.execute_query(query, (board_id,))

    def find_by_card(self, card_id: int) -> List[Dict]:
        query = """
            SELECT l.id, l.name, l.color
            FROM labels l
            JOIN card_labels cl ON l.id = cl.label_id
            WHERE cl.card_id = ?
            ORDER BY l.id ASC
        """
        return self.execute_query(query, (card_id,))

    def attach_to_card(self, card_id: int, label_id: int) -> None:
        with get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO card_labels (card_id, label_id) VALUES (?, ?)",
                    (card_id, label_id),
                )
            except sqlite3.IntegrityError as e:
                raise DuplicateError(str(e)) from e

    def detach_from_card(self, card_id: int, label_id: int) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM card_labels WHERE card_id = ? AND label_id = ?",
                (card_id, label_id),
            )
            return cursor.rowcount
