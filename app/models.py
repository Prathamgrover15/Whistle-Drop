import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class ReportCategory(str, enum.Enum):
    SECURITY = "SECURITY"
    HARASSMENT = "HARASSMENT"
    CORRUPTION = "CORRUPTION"
    TECHNICAL = "TECHNICAL"
    OTHER = "OTHER"


class ReportStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class Moderator(Base):

    __tablename__ = "moderators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_code_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    category: Mapped[ReportCategory] = mapped_column(
        SAEnum(ReportCategory, name="report_category"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_url: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus, name="report_status"), nullable=False, default=ReportStatus.SUBMITTED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    updates: Mapped[list["StatusUpdate"]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="StatusUpdate.created_at"
    )


class StatusUpdate(Base):

    __tablename__ = "status_updates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ReportStatus] = mapped_column(SAEnum(ReportStatus, name="report_status"), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    moderator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("moderators.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    report: Mapped["Report"] = relationship(back_populates="updates")
