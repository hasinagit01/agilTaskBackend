from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateBoardRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class UpdateBoardRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class BoardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_id: int
    created_at: datetime
    updated_at: datetime


class SingleBoardResponse(BaseModel):
    data: BoardResponse


class BoardListResponse(BaseModel):
    data: List[BoardResponse]
