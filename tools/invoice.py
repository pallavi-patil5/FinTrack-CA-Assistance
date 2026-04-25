from config.settings import invoices_col, vendors_col
from datetime import datetime
from tools.vendors import get_or_create_vendor

def get_invoice_category(invoice_type):
    return "Income" if invoice_type == "outgoing" else "Expense"

def create_invoice(data, invoice_type="incoming"):
    vendor_name = data.get("vendor_name", "Unknown")
    get_or_create_vendor(vendor_name)
    
    invoice = {
        "vendor_name": vendor_name,
        "total_amount": data.get("amount", 0),
        "date": data.get("date", ""),
        "due_date": data.get("due_date", ""),
        "status": data.get("status", "Pending"),
        "invoice_type": invoice_type,
        "created_at": datetime.utcnow()
    }
    result = invoices_col.insert_one(invoice)
    return {
        "vendor_name": invoice["vendor_name"],
        "total_amount": invoice["total_amount"],
        "date": invoice["date"],
        "due_date": invoice["due_date"],
        "status": invoice["status"],
        "invoice_type": invoice["invoice_type"],
        "category": get_invoice_category(invoice["invoice_type"]),
        "_id": str(result.inserted_id)
    }

def get_all_invoices():
    invoices = []
    for inv in invoices_col.find():
        status = inv.get("status") or "Pending"
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
            "status": status,
            "invoice_type": invoice_type,
            "category": get_invoice_category(invoice_type)
        })
    return invoices
