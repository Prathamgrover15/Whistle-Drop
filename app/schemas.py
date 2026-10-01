import uuid
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from app.models import ReportCategory, ReportStatus


# ---------- Public: submitting a report ----------

class ReportCreate(BaseModel):
    category: ReportCategory
    description: str = Field(..., min_length=10, max_length=5000)
    evidence_url: str | None = Field(None, max_length=2000)


class ReportCreateResponse(BaseModel):
    case_code: str
    status: ReportStatus
    created_at: datetime
    note: str = "Save this case code now. It is shown only once and cannot be recovered if lost."


# ---------- Public: tracking a report ----------

class TrackRequest(BaseModel):
    case_code: str = Field(..., min_length=5, max_length=100)


class StatusUpdateOut(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    status: ReportStatus
    message: str | None
    created_at: datetime


class TrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: ReportCategory
    description: str
    evidence_url: str | None
    status: ReportStatus
    created_at: datetime
    updates: list[StatusUpdateOut]


# ---------- Moderator auth ----------

class ModeratorLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ModeratorCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=200)


# ---------- Moderator: viewing/managing reports ----------

class ReportSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: ReportCategory
    status: ReportStatus
    created_at: datetime
    updated_at: datetime

class ReportListOut(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ReportSummaryOut]


class ReportDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: ReportCategory
    description: str
    evidence_url: str | None
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    updates: list[StatusUpdateOut]


class ModeratorStatusUpdate(BaseModel):
    status: ReportStatus | None = None
    message: str | None = Field(None, max_length=2000)
