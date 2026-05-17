from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

Role = Literal["member", "viewer"]


class AddMemberRequest(BaseModel):
    user_id: int = Field(gt=0)
    role: Role = "member"


class UpdateMemberRoleRequest(BaseModel):
    role: Role


class MemberResponse(BaseModel):
    board_id: int
    user_id: int
    email: str
    role: str
    created_at: datetime


class MemberListResponse(BaseModel):
    data: List[MemberResponse]
