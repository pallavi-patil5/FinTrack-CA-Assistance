from fastapi import APIRouter
from tools import finance
from tools.bookkeeping import add_transaction, get_all_transactions, get_summary

router = APIRouter()

# ── BOOKKEEPING ──────────────────────────────────────
@router.post("/transactions/add")
def add_txn(data: dict):
    return add_transaction(data["type"], data["amount"], data["category"], data.get("note", ""))

@router.get("/transactions/{user_id}")
def list_txns(user_id: str):
    return {"transactions": get_all_transactions()}

@router.get("/summary/{user_id}")
def summary(user_id: str):
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
