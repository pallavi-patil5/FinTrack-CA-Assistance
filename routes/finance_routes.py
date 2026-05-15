from fastapi import APIRouter
from fastapi.responses import JSONResponse
from tools import finance
from tools.bookkeeping import add_transaction, get_all_transactions, get_summary
from config.settings import transactions_col
from bson import ObjectId

router = APIRouter()

# ── BOOKKEEPING ──────────────────────────────────────
@router.post("/transactions/add")
def add_txn(data: dict):
    return add_transaction(data["type"], data["amount"], data["category"], data.get("note", ""))

@router.put("/transactions/update/{txn_id}")
def update_txn(txn_id: str, data: dict):
    try:
        allowed = {"type", "amount", "category", "note"}
        update = {k: v for k, v in data.items() if k in allowed}
        if "amount" in update:
            update["amount"] = float(update["amount"])
        transactions_col.update_one({"_id": ObjectId(txn_id)}, {"$set": update})
        return {"message": "Updated"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.delete("/transactions/delete/{txn_id}")
def delete_txn(txn_id: str):
    try:
        transactions_col.delete_one({"_id": ObjectId(txn_id)})
        return {"message": "Deleted"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.get("/transactions/{user_id}")
def list_txns(user_id: str):
    return {"transactions": get_all_transactions()}

@router.get("/transactions/admin")
def list_txns_admin():
    return {"transactions": get_all_transactions()}

@router.get("/summary/{user_id}")
def summary(user_id: str):
    return get_summary()

@router.get("/summary/admin")
def summary_admin():
    return get_summary()

# ── FINANCIAL CALCULATIONS ───────────────────────────
@router.post("/calculate/roi")
def roi(data: dict):
    return finance.calculate_roi(data["investment"], data["net_profit"])

@router.post("/calculate/margin")
def margin(data: dict):
    return finance.calculate_profit_margin(data["revenue"], data["cost"])

@router.post("/calculate/cashflow")
def cashflow(data: dict):
    return finance.calculate_cash_flow(data["inflows"], data["outflows"])

@router.post("/calculate/emi")
def emi(data: dict):
    return finance.calculate_emi(data["principal"], data["annual_rate"], data["tenure_months"])

@router.post("/calculate/gst")
def gst(data: dict):
    return finance.calculate_gst(data["amount"], data["rate"], data["inclusive"])
