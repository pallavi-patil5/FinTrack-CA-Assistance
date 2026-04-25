from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from tools.reports import generate_invoice_pdf

router = APIRouter()

@router.get("/report/pdf")
def pdf():
    buf = generate_invoice_pdf()
    return StreamingResponse(buf, media_type="application/pdf")