from dataclasses import dataclass
from datetime import datetime


@dataclass
class Label:
    id: int
    board_id: int
    name: str
    color: str
    created_at: datetime
    updated_at: datetime
