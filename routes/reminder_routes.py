from fastapi import APIRouter
from services.reminder_service import (
    get_upcoming_reminders,
    get_overdue_reminders,
    get_dashboard_data,
    run_daily_reminder_check,
)

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("/upcoming")
def upcoming():
    return {"upcoming": get_upcoming_reminders()}


@router.get("/overdue")
def overdue():
    return {"overdue": get_overdue_reminders()}


@router.get("/dashboard")
def dashboard():
    return get_dashboard_data()


@router.get("/run-check")
def trigger_check():
    """Manually trigger the daily reminder check (useful for testing)."""
    return run_daily_reminder_check()
