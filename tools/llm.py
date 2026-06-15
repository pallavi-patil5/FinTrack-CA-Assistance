import requests
import json
from config.settings import OLLAMA_URL, OLLAMA_MODEL

_EMPTY = {
    "vendor_name": "", "customer_name": "", "gstin": "",
    "invoice_number": "", "invoice_date": "", "due_date": "",
    "cgst": 0.0, "sgst": 0.0, "igst": 0.0,
    "subtotal": 0.0, "total": 0.0,
    "status": "Pending", "line_items": []
}

def _clean(raw: str) -> str:
    """Strip markdown code fences and find the first {...} block."""
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1:
        return raw[start:end + 1]
    return raw.strip()

def parse_invoice(text: str, retries: int = 2) -> dict:
    prompt = f"""Extract invoice details from the text below.
Return ONLY a valid JSON object with these exact fields:
vendor_name, customer_name, gstin, invoice_number, invoice_date, due_date,
cgst, sgst, igst, subtotal, total, status, line_items.

Rules:
- cgst, sgst, igst, subtotal, total must be numbers (0 if not found)
- line_items is an array of {{"description", "quantity", "unit_price", "amount"}}
- status: "Pending", "Paid", or "Overdue"
- Output ONLY the JSON, no explanation, no markdown.

Text:
{text[:3000]}"""

    for attempt in range(1, retries + 1):
        try:
            res = requests.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }, timeout=180)
            res.raise_for_status()
            raw = res.json().get("response", "").strip()
            if not raw:
                print(f"[LLM] Empty response on attempt {attempt}")
                continue
            return json.loads(_clean(raw))
        except json.JSONDecodeError as e:
            print(f"[LLM] JSON parse error attempt {attempt}: {e}")
        except Exception as e:
            print(f"[LLM] Error attempt {attempt}: {e}")

    print("[LLM] All retries failed — returning empty invoice skeleton")
    return dict(_EMPTY)
