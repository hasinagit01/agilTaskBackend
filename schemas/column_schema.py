from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateColumnRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class UpdateColumnRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    position: Optional[int] = Field(default=None, ge=0)


class ReorderColumnsRequest(BaseModel):
    ordered_ids: List[int] = Field(min_length=1)


class ColumnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    board_id: int
    name: str
    position: int
    created_at: datetime
    updated_at: datetime


class SingleColumnResponse(BaseModel):
    data: ColumnResponse


class ColumnListResponse(BaseModel):
    data: List[ColumnResponse]
