from app.models import ReportStatus
from app.routers.moderator import ALLOWED_TRANSITIONS


def test_submitted_can_move_to_under_review_or_dismissed():
    allowed = ALLOWED_TRANSITIONS[ReportStatus.SUBMITTED]
    assert ReportStatus.UNDER_REVIEW in allowed
    assert ReportStatus.DISMISSED in allowed
    assert ReportStatus.RESOLVED not in allowed


def test_under_review_can_move_to_resolved_or_dismissed():
    allowed = ALLOWED_TRANSITIONS[ReportStatus.UNDER_REVIEW]
    assert allowed == {ReportStatus.RESOLVED, ReportStatus.DISMISSED}


def test_resolved_and_dismissed_are_terminal():
    assert ALLOWED_TRANSITIONS[ReportStatus.RESOLVED] == set()
    assert ALLOWED_TRANSITIONS[ReportStatus.DISMISSED] == set()
