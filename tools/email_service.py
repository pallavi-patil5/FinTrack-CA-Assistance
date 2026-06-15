import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "")


def _send(to_email: str, subject: str, body: str) -> bool:
    if not all([SMTP_USER, SMTP_PASS, to_email]):
        print(f"[EMAIL] Skipping — SMTP not configured or no recipient ({to_email!r})")
        return False
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"[EMAIL] Sent '{subject}' → {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Failed: {e}")
        return False


def _days_line(days_remaining: int) -> str:
    if days_remaining < 0:
        return f"Status         : OVERDUE by {abs(days_remaining)} day(s)"
    if days_remaining == 0:
        return "Status         : Due TODAY"
    return f"Days Remaining : {days_remaining}"


def send_outgoing_reminder_to_vendor(to_email: str, invoice_number: str, vendor_name: str,
                                     total_amount: float, due_date: str, days_remaining: int) -> bool:
    """
    Outgoing invoice = I raised the invoice, vendor owes me payment.
    Send mail FROM my email TO vendor asking them to pay.
    """
    body = (
        f"Dear {vendor_name},\n\n"
        f"This is a payment reminder for an invoice raised against you.\n\n"
        f"{'─' * 40}\n"
        f"Invoice Number : {invoice_number}\n"
        f"Vendor         : {vendor_name}\n"
        f"Amount Due     : Rs. {total_amount:.2f}\n"
        f"Due Date       : {due_date}\n"
        f"{_days_line(days_remaining)}\n"
        f"{'─' * 40}\n\n"
        f"Please arrange the payment at the earliest.\n\n"
        f"Regards,\nStartupSarthi"
    )
    return _send(to_email, "Invoice Payment Reminder", body)


def send_incoming_reminder_to_owner(invoice_number: str, vendor_name: str,
                                    total_amount: float, due_date: str, days_remaining: int) -> bool:
    """
    Incoming invoice = vendor sent me an invoice, I owe them payment.
    Send mail TO me (owner/NOTIFY_EMAIL) reminding me to pay.
    """
    body = (
        f"Reminder: You have an outstanding payment to make.\n\n"
        f"{'─' * 40}\n"
        f"Invoice Number : {invoice_number}\n"
        f"Vendor         : {vendor_name}\n"
        f"Amount Due     : Rs. {total_amount:.2f}\n"
        f"Due Date       : {due_date}\n"
        f"{_days_line(days_remaining)}\n"
        f"{'─' * 40}\n\n"
        f"Log in to StartupSarthi to mark it as paid.\n"
    )
    subject = "⚠️ Invoice Overdue — Action Required" if days_remaining < 0 else "Invoice Payment Due — Action Required"
    return _send(NOTIFY_EMAIL, subject, body)
