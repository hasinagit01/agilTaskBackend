from typing import List, Dict
from .base import BaseRepository


class BoardRepository(BaseRepository):
    def __init__(self):
        super().__init__("boards")

    def create(self, name: str, owner_id: int) -> int:
        return self.insert({"name": name, "owner_id": owner_id})

    def update(self, board_id: int, name: str) -> int:
        return self.update_by_id(board_id, {"name": name})

    def find_by_member(self, user_id: int, limit: int, offset: int) -> List[Dict]:
        query = """
            SELECT b.* FROM boards b
            JOIN board_members bm ON b.id = bm.board_id
            WHERE bm.user_id = ?
            ORDER BY b.id DESC LIMIT ? OFFSET ?
        """
        return self.execute_query(query, (user_id, limit, offset))

    def count_by_member(self, user_id: int) -> int:
        query = """
            SELECT COUNT(*) as total FROM boards b
            JOIN board_members bm ON b.id = bm.board_id
            WHERE bm.user_id = ?
        """
        rows = self.execute_query(query, (user_id,))
        return rows[0]["total"] if rows else 0
