from config.settings import transactions_col, invoices_col
from datetime import datetime

def add_transaction(type_, amount, category, note=""):
    txn = {
        "type": type_,
        "amount": float(amount),
        "category": category,
        "note": note,
        "created_at": datetime.utcnow()
    }
    result = transactions_col.insert_one(txn)
    return {
        "_id": str(result.inserted_id),
        "type": txn["type"],
        "amount": txn["amount"],
        "category": txn["category"],
        "note": txn["note"]
    }

def get_all_transactions():
    txns = []
    for t in transactions_col.find().sort("created_at", -1):
        txns.append({
            "_id": str(t["_id"]),
            "type": t.get("type", ""),
            "amount": t.get("amount", 0),
            "category": t.get("category", ""),
            "note": t.get("note", ""),
            "date": t["created_at"].strftime("%Y-%m-%d") if t.get("created_at") else ""
        })
    return txns

def get_summary():
    txns = get_all_transactions()
    income = sum(t["amount"] for t in txns if t["type"] == "Income")
    expense = sum(t["amount"] for t in txns if t["type"] == "Expense")

    # Include invoices in totals
    for inv in invoices_col.find():
        try:
            amount = float(inv.get("total_amount") or 0)
        except:
            amount = 0
        invoice_type = inv.get("invoice_type") or "incoming"
        if invoice_type == "outgoing":
            income += amount
        else:
            expense += amount

    return {
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "net_balance": round(income - expense, 2)
    }
