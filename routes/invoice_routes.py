from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
import shutil
import os

from services.invoice_service import process_invoice
from tools.invoice import get_all_invoices
from tools.reports import generate_invoice_pdf
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
        def f(v):
            try: return round(float(v or 0), 2)
            except: return 0
        invoice_type = inv.get("invoice_type") or "incoming"
        cgst = f(inv.get("cgst"))
        sgst = f(inv.get("sgst"))
        igst = f(inv.get("igst"))
        return {
            "_id": str(inv["_id"]),
            "vendor_name": inv.get("vendor_name") or "Unknown",
            "total_amount": f(inv.get("total_amount")),
            "taxable_amount": f(inv.get("taxable_amount")),
            "gst_rate": f(inv.get("gst_rate")),
            "cgst": cgst, "sgst": sgst, "igst": igst,
            "total_tax": round(cgst + sgst + igst, 2),
            "currency": inv.get("currency") or "INR",
            "payment_terms": inv.get("payment_terms") or "-",
            "org_code": inv.get("org_code") or "-",
            "date": str(inv.get("date") or "-"),
            "due_date": str(inv.get("due_date") or "-"),
            "status": inv.get("status") or "Pending",
            "invoice_type": invoice_type,
            "category": "Income" if invoice_type == "outgoing" else "Expense",
            "line_items": inv.get("line_items") or []
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.put("/invoice/update/{invoice_id}")
def update_invoice(invoice_id: str, data: dict):
    try:
        allowed = {"due_date", "status", "payment_terms", "vendor_name", "date", "total_amount", "currency", "org_code"}
        update = {k: v for k, v in data.items() if k in allowed}
        if not update:
            return JSONResponse(status_code=400, content={"detail": "No valid fields to update"})
        invoices_col.update_one({"_id": ObjectId(invoice_id)}, {"$set": update})
        return {"message": "Invoice updated successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.get("/invoice/pdf/{invoice_id}")
def invoice_pdf(invoice_id: str):
    try:
        inv = invoices_col.find_one({"_id": ObjectId(invoice_id)})
        if not inv:
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        buf = generate_invoice_pdf(inv)
        return StreamingResponse(buf, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="invoice_{invoice_id[-6:]}.pdf"'})
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
