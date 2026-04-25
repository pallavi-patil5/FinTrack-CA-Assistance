from fastapi import APIRouter, Form, Response
from fastapi.responses import RedirectResponse
from config.auth import create_session

router = APIRouter()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

@router.post("/login")
def login(response: Response, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = create_session(username)

        res = RedirectResponse(url="/dashboard", status_code=302)
        res.set_cookie(key="session", value=token, httponly=True)
        return res

    return {"error": "Invalid credentials"}


@router.get("/logout")
def logout():
    res = RedirectResponse(url="/login", status_code=302)
    res.delete_cookie("session")
    return res