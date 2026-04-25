from tools.ocr import extract_text
from tools.llm import parse_invoice
from tools.invoice import create_invoice

def process_invoice(file_path: str, invoice_type="incoming"):
    print(f"[1] OCR starting for: {file_path}")
    raw_text = extract_text(file_path)
    print(f"[2] OCR result: {raw_text[:100]}")

    structured = parse_invoice(raw_text)
    print(f"[3] Parsed data: {structured}")

    invoice = create_invoice(structured, invoice_type=invoice_type)
    print(f"[4] Saved to MongoDB: {invoice}")

    return invoice
