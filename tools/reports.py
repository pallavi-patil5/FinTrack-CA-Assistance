from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import io

def generate_invoice_pdf(inv: dict) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    primary = colors.HexColor("#4f46e5")
    light   = colors.HexColor("#f1f5f9")
    border  = colors.HexColor("#e2e8f0")

    def para(text, size=10, bold=False, color=colors.black, align=None):
        style = ParagraphStyle("x", fontSize=size, fontName="Helvetica-Bold" if bold else "Helvetica",
            textColor=color, alignment=align or 0, leading=size*1.4)
        return Paragraph(str(text or "-"), style)

    def fmt(v):
        try: return f"Rs.{float(v or 0):.2f}"
        except: return "Rs.0.00"

    inv_id = str(inv.get("_id", ""))[-6:].upper()
    elements = []

    # ── HEADER ──────────────────────────────────────────
    header_data = [[
        para("StartupSarthi", 18, bold=True, color=primary),
        para(f"INVOICE #{inv_id}", 16, bold=True, align=TA_RIGHT)
    ]]
    header_table = Table(header_data, colWidths=[90*mm, 90*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4*mm))

    # divider
    div = Table([[""]], colWidths=[180*mm], rowHeights=[1])
    div.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1), primary)]))
    elements.append(div)
    elements.append(Spacer(1, 6*mm))

    # ── VENDOR + INVOICE INFO ────────────────────────────
    info_data = [[
        [para("VENDOR", 8, bold=True, color=colors.HexColor("#64748b")),
         Spacer(1,2), para(inv.get("vendor_name","Unknown"), 11, bold=True),
         Spacer(1,2), para(f"Org Code: {inv.get('org_code','-')}", 9),
         para(f"Currency: {inv.get('currency','INR')}", 9)],
        [para("INVOICE DETAILS", 8, bold=True, color=colors.HexColor("#64748b")),
         Spacer(1,2), para(f"Date: {inv.get('date','-')}", 9),
         para(f"Due Date: {inv.get('due_date','-')}", 9),
         para(f"Payment Terms: {inv.get('payment_terms','-')}", 9),
         Spacer(1,2), para(f"Status: {inv.get('status','Pending')}", 10, bold=True)]
    ]]
    info_table = Table(info_data, colWidths=[90*mm, 90*mm])
    info_table.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("BACKGROUND",(0,0),(-1,-1), light),
        ("BOX",(0,0),(-1,-1),0.5, border),
        ("INNERGRID",(0,0),(-1,-1),0.5, border),
        ("PADDING",(0,0),(-1,-1),8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 6*mm))

    # ── LINE ITEMS ───────────────────────────────────────
    elements.append(para("Invoice Line Items", 11, bold=True))
    elements.append(Spacer(1, 3*mm))

    line_items = inv.get("line_items") or []
    rows = [[para("#",9,bold=True), para("Description",9,bold=True),
             para("Qty",9,bold=True), para("Unit Price",9,bold=True),
             para("Amount",9,bold=True,align=TA_RIGHT)]]

    if line_items:
        for i, it in enumerate(line_items):
            qty   = float(it.get("qty") or 1)
            price = float(it.get("unit_price") or it.get("price") or 0)
            amt   = float(it.get("amount") or qty * price)
            rows.append([
                para(str(i+1), 9),
                para(it.get("description") or "-", 9),
                para(str(qty), 9),
                para(fmt(price), 9),
                para(fmt(amt), 9, align=TA_RIGHT)
            ])
    else:
        rows.append([para("No line items", 9, color=colors.HexColor("#94a3b8")),
                     "", "", "", ""])

    items_table = Table(rows, colWidths=[12*mm, 80*mm, 20*mm, 34*mm, 34*mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0), primary),
        ("TEXTCOLOR",(0,0),(-1,0), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, light]),
        ("BOX",(0,0),(-1,-1),0.5, border),
        ("INNERGRID",(0,0),(-1,-1),0.3, border),
        ("PADDING",(0,0),(-1,-1),7),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("SPAN",(1,len(rows)-1 if not line_items else 99),(4,len(rows)-1 if not line_items else 99)),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 6*mm))

    # ── GST + TOTALS ─────────────────────────────────────
    def f(v):
        try: return round(float(v or 0), 2)
        except: return 0

    cgst = f(inv.get("cgst")); sgst = f(inv.get("sgst")); igst = f(inv.get("igst"))
    total_tax = round(cgst + sgst + igst, 2)
    taxable   = f(inv.get("taxable_amount"))
    total     = f(inv.get("total_amount"))

    totals_data = [
        [para("GST BREAKDOWN", 8, bold=True, color=colors.HexColor("#64748b")), ""],
        [para("Taxable Amount", 9), para(fmt(taxable), 9, align=TA_RIGHT)],
        [para(f"CGST ({f(inv.get('gst_rate'))/2}%)", 9), para(fmt(cgst), 9, align=TA_RIGHT)],
        [para(f"SGST ({f(inv.get('gst_rate'))/2}%)", 9), para(fmt(sgst), 9, align=TA_RIGHT)],
        [para("IGST", 9), para(fmt(igst), 9, align=TA_RIGHT)],
        [para("Total Tax", 9, bold=True), para(fmt(total_tax), 9, bold=True, align=TA_RIGHT)],
        [para("GRAND TOTAL", 11, bold=True, color=primary),
         para(fmt(total), 13, bold=True, color=primary, align=TA_RIGHT)],
    ]
    totals_table = Table(totals_data, colWidths=[120*mm, 60*mm])
    totals_table.setStyle(TableStyle([
        ("SPAN",(0,0),(1,0)),
        ("BACKGROUND",(0,0),(1,0), light),
        ("BACKGROUND",(0,6),(1,6), colors.HexColor("#eef2ff")),
        ("BOX",(0,0),(-1,-1),0.5, border),
        ("INNERGRID",(0,1),(-1,5),0.3, border),
        ("LINEABOVE",(0,6),(1,6),1, primary),
        ("PADDING",(0,0),(-1,-1),7),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    elements.append(totals_table)

    doc.build(elements)
    buf.seek(0)
    return buf
