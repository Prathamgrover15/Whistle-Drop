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
    """
    A moderator account. This is the ONLY place any kind of "identity"
    lives in this schema -- and it belongs to staff, never to a reporter.
    """

    __tablename__ = "moderators"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    """
    A single anonymous report. Notice what's NOT here: no reporter_id,
    no email, no IP address, no session/cookie reference. There is
    nothing in this table (or anywhere else in the schema) that could
    be used to link a report back to the person who filed it.
    """

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # We never store the plaintext case code -- only a SHA-256 hash of it.
    # This mirrors how passwords are stored: even a full database dump
    # doesn't reveal the code, so nobody with DB access (including a
    # careless moderator or an attacker) can look up a specific report
    # unless they already know its code.
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
    """
    A timeline entry for a report. moderator_id is here for internal
    accountability (so staff can tell who changed what) but it is
    NEVER returned to a reporter tracking their case -- see
    schemas.StatusUpdateOut, which simply doesn't include it.
    """

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
