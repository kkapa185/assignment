from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    owner = "Owner"
    editor = "Editor"
    viewer = "Viewer"


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class EventCreate(BaseModel):
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None


class EventOut(EventCreate):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


class ShareUser(BaseModel):
    user_id: int
    role: RoleEnum


class ShareRequest(BaseModel):
    users: List[ShareUser]


class EventPermissionOut(BaseModel):
    user_id: int
    role: RoleEnum

    class Config:
        from_attributes = True
