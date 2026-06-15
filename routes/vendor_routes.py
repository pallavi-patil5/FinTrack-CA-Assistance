from fastapi import APIRouter
from fastapi.responses import JSONResponse
from tools.vendors import get_all_vendors, get_vendor_detail, update_vendor_email

router = APIRouter()

@router.get("/vendors")
def vendors():
    return get_all_vendors()

@router.get("/vendor/{vendor_id}/detail")
def vendor_detail(vendor_id: str):
    data = get_vendor_detail(vendor_id)
    if not data:
        return JSONResponse(status_code=404, content={"detail": "Vendor not found"})
    return data

@router.put("/vendor/{vendor_id}/email")
def set_vendor_email(vendor_id: str, body: dict):
    email = (body.get("email") or "").strip()
    if not email:
        return JSONResponse(status_code=400, content={"detail": "Email required"})
    update_vendor_email(vendor_id, email)
    return {"message": "Vendor email updated", "email": email}