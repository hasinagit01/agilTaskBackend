from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    data: "TokenData"


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


TokenResponse.model_rebuild()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: datetime


class SingleUserResponse(BaseModel):
    data: UserResponse
