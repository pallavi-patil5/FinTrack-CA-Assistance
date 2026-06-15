from datetime import datetime, date
from config.settings import invoices_col, reminders_col
from tools.email_service import send_incoming_reminder_to_owner, send_outgoing_reminder_to_vendor
from tools.vendors import get_vendor_email


def _parse_date(val) -> date | None:
    if not val or str(val).strip() in ("", "None", "-"):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _invoice_snapshot(inv) -> dict:
    return {
        "_id": str(inv["_id"]),
        "invoice_number": inv.get("invoice_number", ""),
        "vendor_name": inv.get("vendor_name", "Unknown"),
        "total_amount": round(float(inv.get("total_amount") or 0), 2),
        "due_date": str(inv.get("due_date") or ""),
        "payment_status": inv.get("payment_status", "Pending"),
    }


def get_dashboard_data() -> dict:
    today = date.today()
    upcoming, overdue = [], []
    total_due_week = 0.0
    total_overdue_amount = 0.0

    for inv in invoices_col.find():
        status = inv.get("payment_status", inv.get("status", "Pending"))
        if status == "Paid":
            continue
        due = _parse_date(inv.get("due_date"))
        if not due:
            continue
        diff = (due - today).days
        snap = _invoice_snapshot(inv)
        snap["days_remaining"] = diff

        if diff < 0:
            snap["payment_status"] = "Overdue"
            overdue.append(snap)
            total_overdue_amount += snap["total_amount"]
        elif diff <= 7:
            upcoming.append(snap)
            total_due_week += snap["total_amount"]

    upcoming.sort(key=lambda x: x["days_remaining"])
    overdue.sort(key=lambda x: x["days_remaining"])

    return {
        "upcoming": upcoming,
        "overdue": overdue,
        "total_due_this_week": round(total_due_week, 2),
        "total_overdue_amount": round(total_overdue_amount, 2),
    }


def get_upcoming_reminders() -> list:
    return get_dashboard_data()["upcoming"]


def get_overdue_reminders() -> list:
    return get_dashboard_data()["overdue"]


def run_daily_reminder_check():
    """Called by scheduler: marks overdue invoices and upserts reminders."""
    today = date.today()
    thresholds = {7, 3, 1}

    for inv in invoices_col.find():
        status = inv.get("payment_status", inv.get("status", "Pending"))
        if status == "Paid":
            continue
        due = _parse_date(inv.get("due_date"))
        if not due:
            continue

        diff = (due - today).days
        inv_id = inv["_id"]

        # Auto-mark overdue
        if diff < 0 and status != "Overdue":
            invoices_col.update_one(
                {"_id": inv_id},
                {"$set": {"payment_status": "Overdue", "status": "Overdue"}},
            )

        # Send email at 7, 3, 1 days before due and once when overdue
        threshold_key = "overdue" if diff < 0 else (str(diff) if diff in thresholds else None)
        if threshold_key:
            label = "Overdue" if diff < 0 else f"Due in {diff} day(s)"
            result = reminders_col.update_one(
                {"invoice_id": str(inv_id), "threshold_key": threshold_key},
                {
                    "$set": {
                        "invoice_id": str(inv_id),
                        "invoice_number": inv.get("invoice_number", ""),
                        "vendor_name": inv.get("vendor_name", "Unknown"),
                        "total_amount": round(float(inv.get("total_amount") or 0), 2),
                        "due_date": str(inv.get("due_date") or ""),
                        "days_remaining": diff,
                        "label": label,
                        "checked_at": datetime.utcnow(),
                    }
                },
                upsert=True,
            )
            if result.upserted_id:
                invoice_number = inv.get("invoice_number", "")
                vendor_name = inv.get("vendor_name", "Unknown")
                total_amount = round(float(inv.get("total_amount") or 0), 2)
                due_date = str(inv.get("due_date") or "")
                invoice_type = inv.get("invoice_type", "incoming")

                if invoice_type == "outgoing":
                    vendor_email = get_vendor_email(vendor_name)
                    if vendor_email:
                        send_outgoing_reminder_to_vendor(
                            to_email=vendor_email,
                            invoice_number=invoice_number,
                            vendor_name=vendor_name,
                            total_amount=total_amount,
                            due_date=due_date,
                            days_remaining=diff,
                        )
                else:
                    send_incoming_reminder_to_owner(
                        invoice_number=invoice_number,
                        vendor_name=vendor_name,
                        total_amount=total_amount,
                        due_date=due_date,
                        days_remaining=diff,
                    )

    return {"status": "done", "checked_at": datetime.utcnow().isoformat()}
