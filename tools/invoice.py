from config.settings import invoices_col, vendors_col
from datetime import datetime
from tools.vendors import get_or_create_vendor

def get_invoice_category(invoice_type):
    return "Income" if invoice_type == "outgoing" else "Expense"

def create_invoice(data, invoice_type="incoming"):
    vendor_name = data.get("vendor_name", "Unknown")
    get_or_create_vendor(vendor_name)
    # LLM may return 'amount' or 'total_amount'
    amount = data.get("total_amount") or data.get("amount") or 0
    try:
        amount = float(amount)
    except:
        amount = 0
    invoice = {
        "vendor_name": vendor_name,
        "total_amount": amount,
        "date": data.get("date", ""),
        "due_date": data.get("due_date", ""),
        "status": data.get("status", "Pending"),
        "invoice_type": invoice_type,
        "category": get_invoice_category(invoice_type),
        "created_at": datetime.utcnow()
    }
    result = invoices_col.insert_one(invoice)
    return {
        "_id": str(result.inserted_id),
        "vendor_name": invoice["vendor_name"],
        "total_amount": invoice["total_amount"],
        "date": invoice["date"],
        "due_date": invoice["due_date"],
        "status": invoice["status"],
        "invoice_type": invoice["invoice_type"],
        "category": get_invoice_category(invoice["invoice_type"])
    }

def resolve_status(status: str, due_date) -> str:
    if status in ("Paid", "Overdue"):
        return status
    try:
        due = datetime.strptime(str(due_date).strip(), "%Y-%m-%d")
        if due.date() < datetime.utcnow().date():
            return "Overdue"
    except:
        pass
    return status or "Pending"

def get_all_invoices():
    invoices = []
    for inv in invoices_col.find():
        invoice_type = inv.get("invoice_type") or "incoming"
        try:
            amount = float(inv.get("total_amount") or 0)
        except:
            amount = 0
        invoices.append({
            "_id": str(inv["_id"]),
            "vendor_name": inv.get("vendor_name") or "Unknown",
            "total_amount": round(amount, 2),
            "date": str(inv.get("date") or ""),
            "due_date": str(inv.get("due_date") or ""),
            "status": resolve_status(inv.get("status"), inv.get("due_date")),
            "invoice_type": invoice_type,
            "category": inv.get("category") or get_invoice_category(invoice_type)
        })
    return invoices
