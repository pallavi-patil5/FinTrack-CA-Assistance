from config.settings import invoices_col

def get_dashboard_summary():
    invoices = list(invoices_col.find())

    total_amount = sum(i["amount"] for i in invoices)
    total_invoices = len(invoices)

    paid = sum(1 for i in invoices if i["status"] == "Paid")
    pending = sum(1 for i in invoices if i["status"] == "Pending")

    return {
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "paid": paid,
        "pending": pending
    }