import requests
import json
from config.settings import OLLAMA_URL, OLLAMA_MODEL

def parse_invoice(text: str):
    prompt = f"""Extract invoice details from the text below and return ONLY a JSON object with these fields: vendor_name, amount, date, due_date, status.

Text:
{text}

Return only the JSON object, no explanation."""

    res = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }, timeout=120)
    res.raise_for_status()

    raw = res.json()["response"].strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
