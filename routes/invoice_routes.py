from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
import shutil
import os

from services.invoice_service import process_invoice
from tools.invoice import get_all_invoices
from config.settings import UPLOAD_DIR, invoices_col
from bson import ObjectId

router = APIRouter()

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/invoices/list/{user_id}")
def invoices(user_id: str):
    return {"invoices": get_all_invoices()}


@router.get("/invoice/detail/{invoice_id}")
def invoice_detail(invoice_id: str):
    try:
        inv = invoices_col.find_one({"_id": ObjectId(invoice_id)})
        if not inv:
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        invoice_type = inv.get("invoice_type") or "incoming"
        return {
            "_id": str(inv["_id"]),
            "vendor_name": inv.get("vendor_name") or "Unknown",
            "total_amount": float(inv.get("total_amount") or 0),
            "date": str(inv.get("date") or "-"),
            "due_date": str(inv.get("due_date") or "-"),
            "status": inv.get("status") or "Pending",
            "invoice_type": invoice_type,
            "category": "Income" if invoice_type == "outgoing" else "Expense"
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...), invoice_type: str = Form("incoming")):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = process_invoice(file_path, invoice_type=invoice_type)
        result.pop("created_at", None)
        result.pop("_id", None)

        return {"message": "Invoice processed successfully", "invoice": result}

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})
