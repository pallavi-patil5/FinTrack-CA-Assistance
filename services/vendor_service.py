from config.settings import vendors_col, invoices_col

def get_vendor_dashboard():
    vendors = list(vendors_col.find())
    result = []

    for v in vendors:
        invs = list(invoices_col.find({"vendor_id": v["_id"]}))

        total_amount = sum(i["amount"] for i in invs)
        total_invoices = len(invs)

        result.append({
            "vendor_id": str(v["_id"]),
            "name": v["name"],
            "total_invoices": total_invoices,
            "total_amount": total_amount
        })

    return result


def get_vendor_detail(vendor_id):
    from bson import ObjectId

    invs = list(invoices_col.find({"vendor_id": ObjectId(vendor_id)}))

    total_amount = sum(i["amount"] for i in invs)
    total_invoices = len(invs)

    overdue = sum(1 for i in invs if i["status"] == "Overdue")
    pending = sum(1 for i in invs if i["status"] == "Pending")

    avg = total_amount / total_invoices if total_invoices else 0

    return {
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "overdue": overdue,
        "pending": pending,
        "avg_amount": round(avg, 2),
        "invoices": [
            {
                "amount": i["amount"],
                "status": i["status"],
                "date": i["date"]
            } for i in invs
        ]
    }