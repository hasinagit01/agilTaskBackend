from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class CreateLabelRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class UpdateLabelRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")


class LabelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    board_id: int
    name: str
    color: str
    created_at: datetime
    updated_at: datetime


class SingleLabelResponse(BaseModel):
    data: LabelResponse


class LabelListResponse(BaseModel):
    data: List[LabelResponse]
