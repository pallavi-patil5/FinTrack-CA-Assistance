from config.settings import invoices_col, vendors_col
from datetime import datetime
from tools.vendors import get_or_create_vendor

def get_invoice_category(invoice_type):
    return "Income" if invoice_type == "outgoing" else "Expense"

def create_invoice(data, invoice_type="incoming", confidence_score: float = 0.0):
    vendor_name = data.get("vendor_name", "Unknown")
    get_or_create_vendor(vendor_name)
    amount = data.get("total") or data.get("total_amount") or data.get("amount") or 0
    try:
        amount = float(amount)
    except:
        amount = 0
    invoice = {
        "vendor_name":    vendor_name,
        "customer_name":  data.get("customer_name", ""),
        "gstin":          data.get("gstin", ""),
        "invoice_number": data.get("invoice_number") or data.get("invoice_no", ""),
        "invoice_date":   data.get("invoice_date") or data.get("date", ""),
        "due_date":       data.get("due_date", ""),
        "cgst":           float(data.get("cgst") or 0),
        "sgst":           float(data.get("sgst") or 0),
        "igst":           float(data.get("igst") or 0),
        "total_tax":      round(float(data.get("cgst") or 0) + float(data.get("sgst") or 0) + float(data.get("igst") or 0), 2),
        "subtotal":       float(data.get("subtotal") or 0),
        "total_amount":   amount,
        "line_items":     data.get("line_items", []),
        "status":         data.get("status", "Pending"),
        "payment_status": "Pending",
        "invoice_type":   invoice_type,
        "category":       get_invoice_category(invoice_type),
        "confidence_score": confidence_score,
        "created_at":     datetime.utcnow()
    }
    result = invoices_col.insert_one(invoice)
    invoice["_id"] = str(result.inserted_id)
    return invoice

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
            "_id":            str(inv["_id"]),
            "vendor_name":    inv.get("vendor_name") or "Unknown",
            "customer_name":  inv.get("customer_name", ""),
            "gstin":          inv.get("gstin", ""),
            "invoice_number": inv.get("invoice_number", ""),
            "date":           str(inv.get("invoice_date") or inv.get("date") or ""),
            "due_date":       str(inv.get("due_date") or ""),
            "cgst":           float(inv.get("cgst") or 0),
            "sgst":           float(inv.get("sgst") or 0),
            "igst":           float(inv.get("igst") or 0),
            "total_tax":      round(float(inv.get("cgst") or 0) + float(inv.get("sgst") or 0) + float(inv.get("igst") or 0), 2),
            "subtotal":       float(inv.get("subtotal") or 0),
            "total_amount":   round(amount, 2),
            "line_items":     inv.get("line_items", []),
            "status":         resolve_status(inv.get("status"), inv.get("due_date")),
            "payment_status": inv.get("payment_status", "Pending"),
            "invoice_type":   invoice_type,
            "category":       inv.get("category") or get_invoice_category(invoice_type),
            "confidence_score": float(inv.get("confidence_score") or 0),
        })
    return invoices
