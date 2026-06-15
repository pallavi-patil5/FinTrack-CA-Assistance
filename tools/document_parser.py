"""
tools/document_parser.py
------------------------
EasyOCR-based invoice field extraction.

Tax extraction handles 3 real-world patterns:
  Pattern 1 — Inline label:   "CGST: 500"  /  "CGST@9%: 115.29"
  Pattern 2 — Rate in label:  "CGST@2.5%: 5.70"  (EatClub style)
  Pattern 3 — Embedded in row: "3665.72/2.5%cGST"  (Amazon style)
  Pattern 4 — Column header:  CGST header row, values below (boAt/D2C style)
  Pattern 5 — Total tax line: "Tax Amount: 922.32"
"""

import re
from typing import Any

import numpy as np
import cv2

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _reader


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Inline / rate-in-label:  "CGST@2.5%: 5.70"  or  "CGST: 500"
_P_CGST_INLINE = re.compile(r"CGST\s*(?:@[\d\.]+%)?\s*[:\-]?\s*([\d,]+\.?\d*)", re.IGNORECASE)
_P_SGST_INLINE = re.compile(r"SGST\s*(?:@[\d\.]+%)?\s*[:\-]?\s*([\d,]+\.?\d*)", re.IGNORECASE)
_P_IGST_INLINE = re.compile(r"IGST\s*(?:@[\d\.]+%)?\s*[:\-]?\s*([\d,]+\.?\d*)", re.IGNORECASE)

# Embedded in product row:  "3665.72/2.5%CGST"  →  capture the amount before it
_P_CGST_EMBED = re.compile(r"([\d,]+\.?\d*)\s*/\s*[\d\.]+%\s*cGST", re.IGNORECASE)
_P_SGST_EMBED = re.compile(r"([\d,]+\.?\d*)\s*/\s*[\d\.]+%\s*sGST", re.IGNORECASE)
_P_IGST_EMBED = re.compile(r"([\d,]+\.?\d*)\s*/\s*[\d\.]+%\s*iGST", re.IGNORECASE)

# Total tax line:  "Tax Amount: 922"  /  "Total Tax: 500"
_P_TAX_TOTAL = re.compile(
    r"(?:total\s*tax|tax\s*amount|total\s*gst)\s*[:\-]?\s*(?:inr|rs\.?)?\s*([\d,]+\.?\d*)",
    re.IGNORECASE,
)

_PATTERNS = {
    "gstin":          re.compile(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b"),
    "invoice_number": re.compile(r"(?:invoice\s*(?:no|number|#)\s*[:\-]?\s*)([A-Z0-9\-\/]+)", re.IGNORECASE),
    "invoice_date":   re.compile(
        r"(?:invoice\s*date|date)\s*[:\-]?\s*"
        r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})",
        re.IGNORECASE,
    ),
    "subtotal":      re.compile(r"(?:sub\s*total|taxable\s*(?:amount|value))\s*[:\-]?\s*([\d,]+\.?\d*)", re.IGNORECASE),
    "total":         re.compile(
        r"(?:grand\s*total|total\s*amount|total\s*payable|net\s*payable|invoice\s*total|total)\s*[:\-;]?\s*(?:inr|rs\.?)?\s*([\d,]+\.?\d*)",
        re.IGNORECASE,
    ),
    "vendor_name":   re.compile(r"(?:sold\s*by|vendor|supplier|from|billed\s*by)\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)", re.IGNORECASE),
    "customer_name": re.compile(r"(?:bill\s*to|buyer|customer|shipped\s*to)\s*[:\-]?\s*([A-Za-z0-9 &.,\-]+)", re.IGNORECASE),
}

_NUM = re.compile(r"[\d,]+\.?\d*")


def _to_float(raw: str) -> float:
    try:
        return float(str(raw).replace(",", "").replace("|", "").replace("{", "").replace("}", "").strip())
    except (ValueError, AttributeError):
        return 0.0


# ---------------------------------------------------------------------------
# Pattern 4: column-header sum (tabular invoices)
# ---------------------------------------------------------------------------

def _col_sum(results: list, header_re: re.Pattern) -> float:
    header_x_centre = None
    header_y_bottom = None

    for (bbox, text, _) in results:
        if header_re.search(text):
            m = header_re.search(text)
            cell_w = bbox[1][0] - bbox[0][0]
            char_w = cell_w / max(len(text), 1)
            header_x_centre = bbox[0][0] + m.start() * char_w + (m.end() - m.start()) * char_w / 2
            header_y_bottom = bbox[2][1]
            break

    if header_x_centre is None:
        return 0.0

    total = 0.0
    for (bbox, text, _) in results:
        if bbox[0][1] < header_y_bottom:
            continue
        x_centre = (bbox[0][0] + bbox[1][0]) / 2
        if abs(x_centre - header_x_centre) > 80:
            continue
        clean = re.sub(r"[^\d.,]", "", text)
        val = _to_float(clean)
        if val >= 100:   # skip percentage-like values (9%, 18% etc.)
            total += val

    return round(total, 2)


# ---------------------------------------------------------------------------
# Main field extractor
# ---------------------------------------------------------------------------

def _extract_fields(full_text: str, results: list) -> tuple[dict, dict]:
    fields: dict[str, Any] = {
        "vendor_name": "", "customer_name": "", "gstin": "",
        "invoice_number": "", "invoice_date": "",
        "cgst": 0.0, "sgst": 0.0, "igst": 0.0,
        "subtotal": 0.0, "total": 0.0, "total_tax": 0.0,
    }
    confidences: dict[str, float] = {k: 0.0 for k in fields}

    # --- non-tax fields via regex ---
    for field, pattern in _PATTERNS.items():
        match = pattern.search(full_text)
        if match:
            raw = match.group(1).strip()
            fields[field] = _to_float(raw) if field in ("subtotal", "total") else raw
            confidences[field] = 1.0 if field == "gstin" else 0.85

    # --- CGST ---
    # Pattern 1 & 2: inline / rate-in-label
    m = _P_CGST_INLINE.search(full_text)
    if m:
        fields["cgst"] = sum(_to_float(x) for x in _P_CGST_INLINE.findall(full_text))
        confidences["cgst"] = 0.90
    # Pattern 3: embedded in product row — sum all occurrences
    elif _P_CGST_EMBED.search(full_text):
        fields["cgst"] = sum(_to_float(x) for x in _P_CGST_EMBED.findall(full_text))
        confidences["cgst"] = 0.80
    # Pattern 4: column header
    else:
        v = _col_sum(results, re.compile(r"\bCGST\b", re.IGNORECASE))
        if v:
            fields["cgst"] = v
            confidences["cgst"] = 0.75

    # --- SGST ---
    m = _P_SGST_INLINE.search(full_text)
    if m:
        fields["sgst"] = sum(_to_float(x) for x in _P_SGST_INLINE.findall(full_text))
        confidences["sgst"] = 0.90
    elif _P_SGST_EMBED.search(full_text):
        fields["sgst"] = sum(_to_float(x) for x in _P_SGST_EMBED.findall(full_text))
        confidences["sgst"] = 0.80
    else:
        v = _col_sum(results, re.compile(r"\bSGST\b", re.IGNORECASE))
        if v:
            fields["sgst"] = v
            confidences["sgst"] = 0.75

    # --- IGST ---
    m = _P_IGST_INLINE.search(full_text)
    if m:
        fields["igst"] = sum(_to_float(x) for x in _P_IGST_INLINE.findall(full_text))
        confidences["igst"] = 0.90
    elif _P_IGST_EMBED.search(full_text):
        fields["igst"] = sum(_to_float(x) for x in _P_IGST_EMBED.findall(full_text))
        confidences["igst"] = 0.80
    else:
        v = _col_sum(results, re.compile(r"\bIGST\b", re.IGNORECASE))
        if v:
            fields["igst"] = v
            confidences["igst"] = 0.75

    # --- total_tax ---
    # Pattern 5: explicit total tax line
    m = _P_TAX_TOTAL.search(full_text)
    if m:
        fields["total_tax"] = _to_float(m.group(1))
        confidences["total_tax"] = 0.90
    else:
        # derive from extracted components
        derived = round(fields["cgst"] + fields["sgst"] + fields["igst"], 2)
        if derived:
            fields["total_tax"] = derived
            confidences["total_tax"] = min(confidences["cgst"], confidences["sgst"]) if fields["igst"] == 0 else confidences["igst"]

    # --- total fallback: largest number on a line containing "total" ---
    if fields["total"] == 0.0:
        for line in reversed(full_text.splitlines()):
            if re.search(r"\btotal\b", line, re.IGNORECASE):
                nums = _NUM.findall(line)
                if nums:
                    fields["total"] = max(_to_float(n) for n in nums)
                    confidences["total"] = 0.70
                    break

    return fields, confidences


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def extract_invoice_layout(image_path: str) -> dict:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot load image from: {image_path}")

    reader = _get_reader()
    results = reader.readtext(
        image_path,
        paragraph=False,
        detail=1,
        contrast_ths=0.1,
        adjust_contrast=0.5,
        width_ths=0.7,
        low_text=0.3,
        text_threshold=0.6,
    )

    results.sort(key=lambda r: (r[0][0][1], r[0][0][0]))

    # Group into lines by Y-centre proximity
    lines: list[list[str]] = []
    current_line: list[str] = []
    last_y = None

    for (bbox, text, conf) in results:
        y_centre = (bbox[0][1] + bbox[2][1]) / 2
        if last_y is None or abs(y_centre - last_y) <= 12:
            current_line.append(text)
        else:
            if current_line:
                lines.append(current_line)
            current_line = [text]
        last_y = y_centre
    if current_line:
        lines.append(current_line)

    full_text = "\n".join(" ".join(l) for l in lines)
    scores = [conf for (_, _, conf) in results]
    ocr_conf = round(float(np.mean(scores)), 4) if scores else 0.0

    fields, field_confs = _extract_fields(full_text, results)
    field_conf = round(float(np.mean(list(field_confs.values()))), 4) if field_confs else 0.0

    return {
        "vendor_name":      fields["vendor_name"],
        "customer_name":    fields["customer_name"],
        "gstin":            fields["gstin"],
        "invoice_number":   fields["invoice_number"],
        "invoice_date":     fields["invoice_date"],
        "cgst":             fields["cgst"],
        "sgst":             fields["sgst"],
        "igst":             fields["igst"],
        "total_tax":        fields["total_tax"],
        "subtotal":         fields["subtotal"],
        "total":            fields["total"],
        "line_items":       [],
        "ocr_confidence":   ocr_conf,
        "field_confidence": field_conf,
        "table_confidence": 0.0,
        "raw_text":         full_text,
    }
