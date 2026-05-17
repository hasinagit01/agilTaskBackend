from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BoardMember:
    board_id: int
    user_id: int
    role: str
    created_at: Optional[datetime] = None
