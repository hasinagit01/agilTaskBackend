from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CreateCardRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None


class UpdateCardRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    position: Optional[int] = Field(default=None, ge=0)
    due_date: Optional[date] = None


class MoveCardRequest(BaseModel):
    target_column_id: int = Field(gt=0)
    position: Optional[int] = Field(default=None, ge=0)


class ReorderCardsRequest(BaseModel):
    ordered_ids: List[int] = Field(min_length=1)


class LabelInfo(BaseModel):
    id: int
    name: str
    color: str


class AssigneeInfo(BaseModel):
    user_id: int
    email: str


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    column_id: int
    title: str
    description: str
    position: int
    due_date: Optional[date] = None
    labels: List[LabelInfo] = []
    assignees: List[AssigneeInfo] = []
    created_at: datetime
    updated_at: datetime


class SingleCardResponse(BaseModel):
    data: CardResponse


class CardListResponse(BaseModel):
    data: List[CardResponse]
