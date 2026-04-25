from config.settings import vendors_col, invoices_col
from bson import ObjectId

def get_or_create_vendor(name):
    vendor = vendors_col.find_one({"name": name})
    if vendor:
        return str(vendor["_id"])
    result = vendors_col.insert_one({"name": name})
    return str(result.inserted_id)

def get_all_vendors():
    vendors = []
    for v in vendors_col.find():
        vid = str(v["_id"])
        invoices = list(invoices_col.find({"vendor_name": v["name"]}))
        total = sum(float(i.get("total_amount") or 0) for i in invoices)
        vendors.append({
            "vendor_id": vid,
            "name": v["name"],
            "total_invoices": len(invoices),
            "total_amount": total
        })
    return vendors

def get_vendor_detail(vendor_id):
    vendor = vendors_col.find_one({"_id": ObjectId(vendor_id)})
    if not vendor:
        return None
    invoices = list(invoices_col.find({"vendor_name": vendor["name"]}))
    amounts = [float(i.get("total_amount") or 0) for i in invoices]
    inv_list = [{
        "id": str(i["_id"]),
        "amount": float(i.get("total_amount") or 0),
        "status": i.get("status") or "Pending",
        "date": str(i.get("date") or ""),
        "invoice_type": i.get("invoice_type") or "incoming",
        "category": "Income" if i.get("invoice_type") == "outgoing" else "Expense"
    } for i in invoices]
    return {
        "name": vendor["name"],
        "total_invoices": len(invoices),
        "total_amount": sum(amounts),
        "avg_amount": round(sum(amounts) / len(amounts), 2) if amounts else 0,
        "pending": sum(1 for i in invoices if i.get("status") == "Pending"),
        "overdue": sum(1 for i in invoices if i.get("status") == "Overdue"),
        "invoices": inv_list
    }