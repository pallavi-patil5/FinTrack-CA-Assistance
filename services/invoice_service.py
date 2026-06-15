import os
from tools.ocr import extract_text
from tools.llm import parse_invoice
from tools.invoice import create_invoice
from tools.preprocessing import preprocess_image
from tools.document_parser import extract_invoice_layout

# File types handled by EasyOCR pipeline
_OCR_EXTS = {".png", ".jpg", ".jpeg", ".pdf"}


def process_invoice(file_path: str, invoice_type="incoming"):
    ext = os.path.splitext(file_path)[1].lower()

    # ------------------------------------------------------------------
    # Path A — image / PDF  →  OpenCV preprocessing → PaddleOCR
    # ------------------------------------------------------------------
    if ext in _OCR_EXTS:
        # Step 0: OpenCV preprocessing
        print(f"[0] Preprocessing: {file_path}")
        preprocess_result = preprocess_image(file_path)
        cleaned_path = preprocess_result["output_path"]
        img_confidence = preprocess_result["confidence"]
        print(f"[0] Preprocessing confidence: {img_confidence}")
        if img_confidence < 0.4:
            print(f"[0] Warning: low image quality ({img_confidence}). OCR accuracy may be reduced.")

        # Step 1: EasyOCR layout + field extraction
        try:
            print(f"[1] EasyOCR extraction: {cleaned_path}")
            ocr_data = extract_invoice_layout(cleaned_path)
            print(f"[1] OCR conf={ocr_data['ocr_confidence']}  "
                  f"field conf={ocr_data['field_confidence']}")
            raw_text = ocr_data["raw_text"]
        finally:
            # Always clean up the temp preprocessed file
            if os.path.exists(cleaned_path):
                os.remove(cleaned_path)

    # ------------------------------------------------------------------
    # Path B — DOCX / TXT  →  direct text extraction (no preprocessing)
    # ------------------------------------------------------------------
    else:
        print(f"[1] Direct text extraction: {file_path}")
        raw_text = extract_text(file_path)
        ocr_data = {}

    # ------------------------------------------------------------------
    # Step 2: LLaMA parse / enrich (uses raw OCR text)
    # ------------------------------------------------------------------
    print(f"[2] Raw text (first 120 chars): {raw_text[:120]}")
    structured = parse_invoice(raw_text)
    print(f"[3] LLaMA parsed: {structured}")

    # Merge PaddleOCR structured fields into LLaMA output —
    # PaddleOCR regex values take precedence for numeric/validated fields
    # because they are extracted directly from layout, not inferred.
    for field in ("gstin", "invoice_number", "invoice_date",
                  "cgst", "sgst", "igst", "subtotal", "line_items"):
        ocr_val = ocr_data.get(field)
        if ocr_val not in (None, "", 0, 0.0, []):
            structured[field] = ocr_val

    # ------------------------------------------------------------------
    # Step 3: Persist to MongoDB
    # ------------------------------------------------------------------
    invoice = create_invoice(structured, invoice_type=invoice_type,
                              confidence_score=ocr_data.get("ocr_confidence", 0.0))
    print(f"[4] Saved to MongoDB: {invoice}")

    return invoice
