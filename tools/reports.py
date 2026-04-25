from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from config.settings import invoices_col

def generate_invoice_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    y = 750
    for inv in invoices_col.find():
        c.drawString(50, y, f"Amount: {inv['amount']}")
        y -= 20

    c.save()
    buffer.seek(0)
    return buffer