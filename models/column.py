from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Column:
    id: Optional[int]
    board_id: int
    name: str
    position: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
