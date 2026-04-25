from fastapi import APIRouter
from tools import chatbot

router = APIRouter()

@router.post("/chat")
def chat(data: dict):
    res = chatbot.get_chat_response(data["message"], [])
    return {"response": res}