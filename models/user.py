from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    email: str
    password_hash: str
    created_at: Optional[datetime] = None
