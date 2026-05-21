from typing import Optional, Dict, List
from .base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")

    def create(self, email: str, password_hash: str,
               firstname: Optional[str] = None, name: Optional[str] = None) -> int:
        data = {"email": email, "password_hash": password_hash}
        if firstname is not None:
            data["firstname"] = firstname
        if name is not None:
            data["name"] = name
        return self.insert(data)

    def find_by_email(self, email: str) -> Optional[Dict]:
        rows = self.find_by({"email": email})
        return rows[0] if rows else None

    def search_by_email(self, query: str, limit: int = 10) -> List[Dict]:
        sql = "SELECT id, email, firstname, name FROM users WHERE email LIKE ? ORDER BY email LIMIT ?"
        return self.execute_query(sql, (f"%{query}%", limit))

    def update_email(self, user_id: int, email: str) -> None:
        self.execute_command("UPDATE users SET email = ? WHERE id = ?", (email, user_id))

    def update_password(self, user_id: int, password_hash: str) -> None:
        self.execute_command("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))

    def update_profile(self, user_id: int, firstname: Optional[str], name: Optional[str]) -> None:
        self.execute_command(
            "UPDATE users SET firstname = ?, name = ? WHERE id = ?",
            (firstname, name, user_id),
        )

    def delete_user(self, user_id: int) -> None:
        self.execute_command("DELETE FROM users WHERE id = ?", (user_id,))
