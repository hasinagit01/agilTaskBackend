from typing import List, Dict
from .base import BaseRepository
from ..connection import get_connection


class ColumnRepository(BaseRepository):
    def __init__(self):
        super().__init__("columns")

    def create(self, board_id: int, name: str, position: int) -> int:
        return self.insert({"board_id": board_id, "name": name, "position": position})

    def update(self, column_id: int, name: str, position: int) -> int:
        return self.update_by_id(column_id, {"name": name, "position": position})

    def find_by_board(self, board_id: int) -> List[Dict]:
        query = f"SELECT * FROM {self.table_name} WHERE board_id = ? ORDER BY position ASC"
        return self.execute_query(query, (board_id,))

    def count_by_board(self, board_id: int) -> int:
        return self.count({"board_id": board_id})

    def reorder(self, board_id: int, ordered_ids: List[int]) -> None:
        with get_connection() as conn:
            for pos, col_id in enumerate(ordered_ids):
                conn.execute(
                    "UPDATE columns SET position = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND board_id = ?",
                    (pos, col_id, board_id),
                )
