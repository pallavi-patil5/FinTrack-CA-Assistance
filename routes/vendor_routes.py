from fastapi import APIRouter
from fastapi.responses import JSONResponse
from tools.vendors import get_all_vendors, get_vendor_detail

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