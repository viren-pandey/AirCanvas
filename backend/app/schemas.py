from __future__ import annotations

import importlib.util
import uuid
from typing import Any, Literal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

if importlib.util.find_spec("email_validator") is not None:
    from pydantic import EmailStr

    EmailType = EmailStr
else:  # pragma: no cover - offline/local fallback
    EmailType = str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailType
    is_admin: bool
    created_at: datetime


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailType
    password: str = Field(min_length=8, max_length=128)
    admin_secret: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("Invalid email")
        return email


class LoginRequest(BaseModel):
    email: EmailType
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("Invalid email")
        return email


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SessionCreateRequest(BaseModel):
    session_start: datetime | None = None


class SessionEndRequest(BaseModel):
    session_end: datetime | None = None
    avg_fps: float | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    session_start: datetime
    session_end: datetime | None
    avg_fps: float | None


class FrameUploadUrlRequest(BaseModel):
    session_id: uuid.UUID | None = None
    brush_mode: str | None = Field(default="brush")
    shape_mode: str | None = Field(default="free_draw")
    frame_extension: str = "png"
    thumbnail_extension: str = "jpg"


class FrameUploadUrlResponse(BaseModel):
    frame_id: uuid.UUID
    frame_object_key: str
    thumbnail_object_key: str
    frame_upload_url: str
    thumbnail_upload_url: str
    expires_in: int


class FrameCompleteResponse(BaseModel):
    id: uuid.UUID
    frame_url: str
    thumbnail_url: str | None
    created_at: datetime


class FrameOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    session_id: uuid.UUID | None
    frame_url: str
    thumbnail_url: str | None
    created_at: datetime
    brush_mode: str | None
    shape_mode: str | None


class FramesPage(BaseModel):
    total: int
    items: list[FrameOut]


class FramesPerUserItem(BaseModel):
    user_id: uuid.UUID
    name: str
    frames: int


class AdminMetrics(BaseModel):
    total_users: int
    total_drawings: int
    average_session_duration_seconds: float
    frames_per_user: list[FramesPerUserItem]


class RecentActivityItem(BaseModel):
    frame_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    created_at: datetime
    brush_mode: str | None
    shape_mode: str | None
    preview_url: str | None


class RecentActivityResponse(BaseModel):
    items: list[RecentActivityItem]


class CommunityPostCreate(BaseModel):
    title: str = Field(default="", max_length=220)
    content: str = Field(min_length=1, max_length=2400)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return value.strip()

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Post content cannot be empty")
        return text


class CommunityPostOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    title: str
    content: str
    score: int
    comment_count: int
    user_vote: int = 0
    created_at: datetime


class CommunityPostsPage(BaseModel):
    total: int
    items: list[CommunityPostOut]


class CommunityVoteRequest(BaseModel):
    value: Literal[-1, 0, 1]


class CommunityCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1200)
    parent_comment_id: uuid.UUID | None = None

    @field_validator("content")
    @classmethod
    def normalize_comment(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("Comment cannot be empty")
        return text


class CommunityCommentOut(BaseModel):
    id: uuid.UUID
    post_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    parent_comment_id: uuid.UUID | None
    content: str
    created_at: datetime


class CommunityCommentsPage(BaseModel):
    total: int
    items: list[CommunityCommentOut]


class ActivityEventOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    activity_type: str
    details: dict[str, Any] | None
    created_at: datetime


class ActivityEventsPage(BaseModel):
    total: int
    items: list[ActivityEventOut]


class DesktopLaunchResponse(BaseModel):
    started: bool
    already_running: bool
    pid: int | None
    message: str

# ---- Pydantic v2 forward ref fix ----
FrameUploadUrlRequest.model_rebuild()
FrameUploadUrlResponse.model_rebuild()
FrameCompleteResponse.model_rebuild()
FrameOut.model_rebuild()
FramesPage.model_rebuild()
CommunityPostCreate.model_rebuild()
CommunityPostOut.model_rebuild()
CommunityPostsPage.model_rebuild()
CommunityVoteRequest.model_rebuild()
CommunityCommentCreate.model_rebuild()
CommunityCommentOut.model_rebuild()
CommunityCommentsPage.model_rebuild()
ActivityEventOut.model_rebuild()
ActivityEventsPage.model_rebuild()
DesktopLaunchResponse.model_rebuild()
