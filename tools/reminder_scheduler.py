from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from services.reminder_service import run_daily_reminder_check, _parse_date
from tools.email_service import send_outgoing_reminder_to_vendor, send_incoming_reminder_to_owner
from tools.vendors import get_vendor_email
from config.settings import invoices_col
from datetime import date


REMINDER_THRESHOLDS = {7, 3, 1}


def daily_job():
    print("[SCHEDULER] Running daily reminder check...")
    run_daily_reminder_check()

    today = date.today()

    for inv in invoices_col.find():
        status = inv.get("payment_status", inv.get("status", "Pending"))
        if status == "Paid":
            continue
        due = _parse_date(inv.get("due_date"))
        if not due:
            continue

        diff = (due - today).days
        # Only act on overdue or threshold days
        if diff >= 0 and diff not in REMINDER_THRESHOLDS:
            continue

        invoice_type = inv.get("invoice_type", "incoming")
        vendor_name = inv.get("vendor_name", "Unknown")
        kwargs = dict(
            invoice_number=inv.get("invoice_number", "N/A"),
            vendor_name=vendor_name,
            total_amount=round(float(inv.get("total_amount") or 0), 2),
            due_date=str(inv.get("due_date") or ""),
            days_remaining=diff,
        )

        if invoice_type == "outgoing":
            # I raised this invoice — vendor owes me — email vendor to pay
            vendor_email = get_vendor_email(vendor_name)
            if vendor_email:
                send_outgoing_reminder_to_vendor(to_email=vendor_email, **kwargs)
            else:
                print(f"[SCHEDULER] No vendor email for '{vendor_name}', skipping outgoing reminder.")
        else:
            # Incoming invoice — I owe the vendor — email me to pay
            send_incoming_reminder_to_owner(**kwargs)

    print("[SCHEDULER] Done.")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(daily_job, CronTrigger(hour=8, minute=0))
    scheduler.start()
    print("[SCHEDULER] Reminder scheduler started (daily at 08:00).")
    return scheduler
