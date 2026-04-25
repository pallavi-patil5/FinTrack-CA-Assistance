from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from config.auth import verify_session

from routes import (
    invoice_routes,
    vendor_routes,
    finance_routes,
    report_routes,
    auth_routes,
    chat_routes
)

app = FastAPI()

# ---------------------------
# STATIC FILES
# ---------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------
# MIDDLEWARE
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# 🔐 AUTH CHECK FUNCTION
# ---------------------------
def check_auth(request: Request):
    token = request.cookies.get("session")
    if not token or not verify_session(token):
        return False
    return True


# ---------------------------
# 🔁 AUTO REDIRECT ROOT
# ---------------------------
@app.get("/", response_class=HTMLResponse)
def root():
    return RedirectResponse("/login")


# ---------------------------
# 🔐 LOGIN PAGE
# ---------------------------
@app.get("/login", response_class=HTMLResponse)
def login_page():
    return open("templates/login.html").read()


# ---------------------------
# 🔐 PROTECTED DASHBOARD
# ---------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if not check_auth(request):
        return RedirectResponse("/login")

    return open("templates/index.html").read()


# ---------------------------
# 🔐 PROTECTED INVOICE PAGE
# ---------------------------
@app.get("/invoice/{invoice_id}", response_class=HTMLResponse)
def invoice_page(invoice_id: str, request: Request):
    if not check_auth(request):
        return RedirectResponse("/login")

    return open("templates/invoice_detail.html").read()


# ---------------------------
# 🔐 PROTECTED VENDOR PAGE
# ---------------------------
@app.get("/vendors-page", response_class=HTMLResponse)
def vendors_page(request: Request):
    if not check_auth(request):
        return RedirectResponse("/login")

    return open("templates/vendors.html").read()


# ---------------------------
# ROUTES
# ---------------------------
app.include_router(invoice_routes.router)
app.include_router(vendor_routes.router)
app.include_router(finance_routes.router)
app.include_router(report_routes.router)
app.include_router(auth_routes.router)
app.include_router(chat_routes.router)


# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
