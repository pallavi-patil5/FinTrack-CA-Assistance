# 🚀 StartupSarthi

> AI-powered financial management platform for startups — invoice OCR, bookkeeping, vendor tracking, financial calculations, and automated due-date reminders in one dashboard.

---

## ✨ Features

| Module | Description |
|---|---|
| 📄 Invoice Management | Upload invoices via OCR, extract data using LLaMA 3, store in MongoDB |
| 🏢 Vendor Tracking | Auto-create vendors from invoices, store vendor email, view per-vendor invoice history and stats |
| 💰 Bookkeeping | Add income/expense transactions, view balance summary |
| 📊 Financial Calculations | ROI, Profit Margin, Cash Flow, Loan EMI, GST computation |
| 🤖 AI Chatbot | Ask financial questions powered by local LLaMA 3 via Ollama |
| 🔐 Authentication | Session-based login with cookie auth |
| 🔔 Due-Date Reminders | Automatic daily reminders at 7, 3, 1 days before due date and on overdue |
| 📧 Email Notifications | Outgoing invoices → reminder sent to vendor; Incoming invoices → reminder sent to you |

---

## 🛠 Tech Stack

- **Backend** — FastAPI (Python)
- **Database** — MongoDB (local)
- **OCR** — Tesseract OCR + Pillow
- **AI/LLM** — Ollama (LLaMA 3) — runs fully local, no API key needed
- **Scheduler** — APScheduler (daily background job)
- **Email** — Python smtplib via Gmail SMTP
- **Frontend** — Vanilla HTML/CSS/JS with Chart.js and Lucide icons

---

## 📁 Project Structure

```
EDAI6/
├── config/
│   ├── auth.py                # Session auth
│   └── settings.py            # MongoDB + env config
├── models/
│   └── schemas.py             # Pydantic models
├── routes/
│   ├── auth_routes.py
│   ├── chat_routes.py
│   ├── finance_routes.py      # Bookkeeping + calculations
│   ├── invoice_routes.py
│   ├── reminder_routes.py     # Due-date reminder APIs
│   ├── report_routes.py
│   └── vendor_routes.py
├── services/
│   ├── invoice_service.py
│   ├── reminder_service.py    # Reminder query + overdue marking logic
│   └── vendor_service.py
├── static/
│   ├── css/styles.css
│   └── js/dashboard.js
├── templates/
│   ├── index.html
│   ├── invoice_detail.html
│   └── login.html
├── tools/
│   ├── bookkeeping.py         # Transaction CRUD
│   ├── chatbot.py             # Ollama chat
│   ├── email_service.py       # Gmail SMTP email sender
│   ├── finance.py             # ROI, EMI, GST, etc.
│   ├── invoice.py             # Invoice CRUD
│   ├── llm.py                 # LLM invoice parsing
│   ├── ocr.py                 # Tesseract OCR
│   ├── reminder_scheduler.py  # APScheduler daily job
│   ├── reports.py             # PDF generation
│   └── vendors.py             # Vendor CRUD
├── uploads/                   # Uploaded invoice files (gitignored)
├── .env                       # Environment variables (gitignored)
├── main.py                    # FastAPI app entry point
└── requirements.txt
```

---

## ⚙️ Setup

### Prerequisites

| Tool | Download |
|---|---|
| Python 3.10+ | https://python.org |
| MongoDB Community | https://www.mongodb.com/try/download/community |
| Tesseract OCR | https://github.com/UB-Mannheim/tesseract/wiki |
| Ollama | https://ollama.com |

---

### 1. Clone the repository

```bash
git clone https://github.com/your-username/startupsarthi.git
cd startupsarthi
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env` file in the root directory:

```env
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=EDAI6

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3

TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

UPLOAD_DIR=uploads
SECRET_KEY=your-secret-key-here

# Email / SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
NOTIFY_EMAIL=your-gmail@gmail.com
```

### 5. Gmail App Password setup

Gmail requires an App Password for SMTP (your regular password will not work):

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Enable **2-Step Verification** under Security
3. Search **App passwords** → Select app: Mail, device: Windows Computer
4. Copy the generated 16-character password into `SMTP_PASS`

### 6. Install and start Ollama

```bash
# Pull LLaMA 3 model (one-time, ~4GB)
ollama pull llama3

# Start Ollama server (keep this running)
ollama serve
```

### 7. Start MongoDB

MongoDB runs as a Windows service automatically after installation. To verify:

```bash
mongosh
```

### 8. Run the application

```bash
python main.py
```

Visit **http://localhost:8000** in your browser.

Default credentials:
- Username: `admin`
- Password: `admin123`

---

## 🗄️ MongoDB Collections

| Collection | Description |
|---|---|
| `invoices` | Uploaded invoices with OCR-extracted data, GST breakdown, and `payment_status` |
| `vendors` | Auto-created vendor records including `email` field |
| `transactions` | Income and expense transactions |
| `reminders` | Auto-generated reminder records per invoice per threshold |

---

## 🔔 Reminder & Email System

### How it works

The scheduler runs **every day at 08:00 AM** and checks all unpaid invoices.

| Days Remaining | Action |
|---|---|
| 7, 3, 1 days before due | Send reminder email |
| Overdue (`today > due_date`) | Mark invoice as `Overdue` in MongoDB + send email |

### Email routing logic

| Invoice Type | Meaning | Email sent to |
|---|---|---|
| `outgoing` | I raised the invoice — vendor owes me | Vendor's email (set in vendor panel) |
| `incoming` | Vendor raised the invoice — I owe them | Me (`NOTIFY_EMAIL`) |

### Setting vendor email

Open the **Vendors** section → click any vendor → enter email in the **Vendor Email** field → click **Save**.

### Manual trigger (for testing)

```
POST http://localhost:8000/reminders/run-check
```

---

## 📌 API Endpoints

### Invoices
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/invoices/list/{user_id}` | List all invoices |
| `GET` | `/invoice/detail/{id}` | Get single invoice detail |
| `POST` | `/upload-invoice` | Upload and process invoice via OCR + LLM |

### Vendors
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/vendors` | List all vendors with stats |
| `GET` | `/vendor/{id}/detail` | Get vendor detail with invoice history |
| `PUT` | `/vendor/{id}/email` | Set or update vendor email |

### Transactions & Summary
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/summary/{user_id}` | Income/expense/balance summary |
| `GET` | `/transactions/{user_id}` | List all transactions |
| `POST` | `/transactions/add` | Add new transaction |

### Financial Calculations
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/calculate/roi` | Return on Investment |
| `POST` | `/calculate/margin` | Profit margin |
| `POST` | `/calculate/cashflow` | Cash flow analysis |
| `POST` | `/calculate/emi` | Loan EMI calculator |
| `POST` | `/calculate/gst` | GST computation |

### Reminders
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/reminders/upcoming` | Invoices due within 7 days |
| `GET` | `/reminders/overdue` | All overdue invoices |
| `GET` | `/reminders/dashboard` | Combined summary with totals |
| `POST` | `/reminders/run-check` | Manually trigger daily reminder job |

### Chat
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | AI chatbot (LLaMA 3 via Ollama) |

---

## 🔒 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017/` |
| `DATABASE_NAME` | MongoDB database name | `EDAI6` |
| `ADMIN_USERNAME` | Login username | `admin` |
| `ADMIN_PASSWORD` | Login password | `admin123` |
| `OLLAMA_URL` | Ollama API endpoint | `http://localhost:11434/api/generate` |
| `OLLAMA_MODEL` | LLM model name | `llama3` |
| `TESSERACT_PATH` | Path to Tesseract executable | `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| `SECRET_KEY` | Session signing key | — |
| `SMTP_HOST` | SMTP server host | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | Gmail address used to send emails | — |
| `SMTP_PASS` | Gmail App Password (16-char) | — |
| `NOTIFY_EMAIL` | Your email — receives incoming invoice reminders | — |

---

## 📄 License

MIT License — free to use and modify.
