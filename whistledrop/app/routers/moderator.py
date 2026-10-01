import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_moderator
from app.models import Report, StatusUpdate, ReportStatus, ReportCategory, Moderator
from app.schemas import ReportSummaryOut, ReportListOut, ReportDetailOut, ModeratorStatusUpdate 

router = APIRouter(prefix="/moderator/reports", tags=["moderator"])

# The only status changes allowed. RESOLVED and DISMISSED are terminal --
# once a case is closed it stays closed, which matches the workflow in
# the spec (SUBMITTED -> UNDER_REVIEW -> RESOLVED / DISMISSED).
ALLOWED_TRANSITIONS: dict[ReportStatus, set[ReportStatus]] = {
    ReportStatus.SUBMITTED: {ReportStatus.UNDER_REVIEW, ReportStatus.DISMISSED},
    ReportStatus.UNDER_REVIEW: {ReportStatus.RESOLVED, ReportStatus.DISMISSED},
    ReportStatus.RESOLVED: set(),
    ReportStatus.DISMISSED: set(),
}


@router.get("", response_model=ReportListOut)
async def list_reports(
    category: ReportCategory | None = Query(None),
    status_filter: ReportStatus | None = Query(None, alias="status"),
    search: str | None = Query(None, min_length=1, max_length=200, description="Case-insensitive text search within the description"),
    limit: int = Query(50, ge=1, le=200, description="Max reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip, for paging"),
    db: AsyncSession = Depends(get_db),
    _: Moderator = Depends(get_current_moderator),
):
    stmt = select(Report)
    count_stmt = select(func.count()).select_from(Report)

    if category is not None:
        stmt = stmt.where(Report.category == category)
        count_stmt = count_stmt.where(Report.category == category)
    if status_filter is not None:
        stmt = stmt.where(Report.status == status_filter)
        count_stmt = count_stmt.where(Report.status == status_filter)
    if search is not None:
        stmt = stmt.where(Report.description.ilike(f"%{search}%"))
        count_stmt = count_stmt.where(Report.description.ilike(f"%{search}%"))

    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Report.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return ReportListOut(total=total, limit=limit, offset=offset, items=items)


@router.get("/{report_id}", response_model=ReportDetailOut)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Moderator = Depends(get_current_moderator),
):
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.refresh(report, attribute_names=["updates"])
    return report


@router.patch("/{report_id}", response_model=ReportDetailOut)
async def update_report(
    report_id: uuid.UUID,
    payload: ModeratorStatusUpdate,
    db: AsyncSession = Depends(get_db),
    moderator: Moderator = Depends(get_current_moderator),
):
    if payload.status is None and not payload.message:
        raise HTTPException(status_code=422, detail="Provide a new status, a message, or both")

    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    new_status = report.status
    if payload.status is not None and payload.status != report.status:
        if payload.status not in ALLOWED_TRANSITIONS[report.status]:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot move a report from {report.status.value} to {payload.status.value}",
            )
        new_status = payload.status
        report.status = new_status

    # moderator_id is recorded for internal accountability only -- it
    # is never included in what a reporter sees (see StatusUpdateOut).
    db.add(StatusUpdate(report_id=report.id, status=new_status, message=payload.message, moderator_id=moderator.id))
    await db.commit()
    await db.refresh(report, attribute_names=["updates"])
    return report
