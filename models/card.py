from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Card:
    id: Optional[int]
    column_id: int
    title: str
    description: str
    position: int
    due_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
