from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Report, StatusUpdate, ReportStatus
from app.schemas import ReportCreate, ReportCreateResponse, TrackRequest, TrackResponse
from app.security import generate_case_code, hash_case_code

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportCreateResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(payload: ReportCreate, db: AsyncSession = Depends(get_db)):
    for _ in range(5):
        case_code = generate_case_code()
        case_code_hash = hash_case_code(case_code)
        existing = await db.execute(select(Report.id).where(Report.case_code_hash == case_code_hash))
        if existing.scalar_one_or_none() is None:
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate a unique case code, please retry")

    report = Report(
        case_code_hash=case_code_hash,
        category=payload.category,
        description=payload.description,
        evidence_url=payload.evidence_url,
    )
    db.add(report)
    await db.flush()  # get report.id without committing yet

    db.add(StatusUpdate(report_id=report.id, status=ReportStatus.SUBMITTED, message="Report submitted."))
    await db.commit()
    await db.refresh(report)
    return ReportCreateResponse(case_code=case_code, status=report.status, created_at=report.created_at)


@router.post("/track", response_model=TrackResponse)
async def track_report(payload: TrackRequest, db: AsyncSession = Depends(get_db)):
    case_code_hash = hash_case_code(payload.case_code.strip())
    result = await db.execute(select(Report).where(Report.case_code_hash == case_code_hash))
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No report found for that case code")

    await db.refresh(report, attribute_names=["updates"])
    return report
