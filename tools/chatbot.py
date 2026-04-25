import requests
from config.settings import OLLAMA_URL, OLLAMA_MODEL

chat_store = {}

def get_chat_response(message, history):
    res = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": message,
        "stream": False
    }, timeout=120)
    res.raise_for_status()
    return res.json()["response"].strip()

def save_chat(user_id, msg, res):
    chat_store.setdefault(user_id, []).append({"q": msg, "a": res})

def get_chat_history(user_id):
    return chat_store.get(user_id, [])