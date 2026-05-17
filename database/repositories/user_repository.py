from typing import Optional, Dict
from .base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")

    def create(self, email: str, password_hash: str) -> int:
        return self.insert({"email": email, "password_hash": password_hash})

    def find_by_email(self, email: str) -> Optional[Dict]:
        rows = self.find_by({"email": email})
        return rows[0] if rows else None
