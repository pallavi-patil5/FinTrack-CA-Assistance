from pydantic import BaseModel
from typing import List, Optional

class InvoiceItem(BaseModel):
    name: str
    quantity: float
    unit_price: float

class Invoice(BaseModel):
    vendor_name: str
    amount: float
    date: str
    due_date: Optional[str] = None
    status: Optional[str] = "Pending"
    invoice_type: Optional[str] = "incoming"

class Vendor(BaseModel):
    name: str