# StartupSarthi

AI-powered financial management platform for startups. Automates invoice processing via OCR and LLM, tracks vendors, manages bookkeeping, computes GST and financial metrics, and sends automated due-date email reminders — all from a single dashboard.

---

## Features

- **Invoice OCR Pipeline** — Upload PDF/image invoices; OpenCV preprocessing → EasyOCR extraction → LLaMA 3 parsing extracts vendor, GSTIN, tax breakdown, line items with confidence scoring
- **Vendor Management** — Auto-creates vendors from invoices; supports email assignment and per-vendor invoice history
- **Bookkeeping** — Add, edit, and delete income/expense transactions; view income/expense/balance summary
- **Financial Calculators** — ROI, profit margin, cash flow, loan EMI, GST (inclusive/exclusive)
- **Due-Date Reminders** — APScheduler job runs daily at 08:00; sends email reminders at 7, 3, and 1 day(s) before due date and marks overdue invoices
- **AI Chatbot** — Financial Q&A powered by LLaMA 3 running locally via Ollama
- **PDF Reports** — Generate downloadable financial reports via ReportLab
- **Session Auth** — Cookie-based login with itsdangerous-signed sessions

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn (Python 3.10+) |
| Database | MongoDB (PyMongo) |
| OCR | OpenCV preprocessing + EasyOCR |
| PDF parsing | PyMuPDF (fitz) |
| AI / LLM | Ollama — LLaMA 3 (local, no API key) |
| Scheduler | APScheduler |
| Email | Python smtplib — Gmail SMTP (TLS) |
| Frontend | Vanilla HTML / CSS / JS + Chart.js + Lucide icons |

---

## Project Structure

```
EDAI6/
├── config/
│   ├── auth.py                # Session signing & verification
│   └── settings.py            # Env config + MongoDB collections
├── models/
│   └── schemas.py             # Pydantic request/response models
├── routes/
│   ├── auth_routes.py         # Login / logout
│   ├── chat_routes.py         # AI chatbot endpoint
│   ├── finance_routes.py      # Bookkeeping CRUD + financial calculators
│   ├── invoice_routes.py      # Invoice upload, list, detail
│   ├── reminder_routes.py     # Reminder queries + manual trigger
│   ├── report_routes.py       # PDF report generation
│   └── vendor_routes.py       # Vendor list, detail, email update
├── services/
│   ├── invoice_service.py     # End-to-end OCR → LLM → MongoDB pipeline
│   └── reminder_service.py    # Reminder query & overdue marking logic
├── static/
│   ├── css/styles.css
│   └── js/dashboard.js
├── templates/
│   ├── index.html             # Main dashboard
│   ├── invoice_detail.html
│   ├── vendors.html
│   └── login.html
├── tools/
│   ├── bookkeeping.py         # Transaction CRUD helpers
│   ├── chatbot.py             # Ollama chat wrapper
│   ├── document_parser.py     # EasyOCR layout + multi-pattern field extractor
│   ├── email_service.py       # Gmail SMTP sender
│   ├── finance.py             # ROI, EMI, GST, margin, cash flow
│   ├── invoice.py             # Invoice CRUD helpers
│   ├── llm.py                 # LLaMA 3 invoice parser
│   ├── ocr.py                 # Plain text extraction (DOCX / TXT)
│   ├── preprocessing.py       # OpenCV image preprocessing pipeline
│   ├── reminder_scheduler.py  # APScheduler daily job setup
│   ├── reports.py             # ReportLab PDF generation
│   └── vendors.py             # Vendor CRUD helpers
├── uploads/                   # Uploaded invoice files (gitignored)
├── .env                       # Environment variables (gitignored)
├── main.py                    # FastAPI app entry point
├── requirements.txt
└── test.py                    # Pipeline health-check script
```

---

## Prerequisites

| Tool | Version | Link |
|---|---|---|
| Python | 3.10+ | https://python.org |
| MongoDB Community | Any recent | https://www.mongodb.com/try/download/community |
| Ollama | Latest | https://ollama.com |

> Tesseract OCR is **not required** — the pipeline uses EasyOCR.

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/your-username/startupsarthi.git
cd startupsarthi

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in the project root:

```env
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=EDAI6

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3

UPLOAD_DIR=uploads
SECRET_KEY=your-secret-key-here

# Gmail SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
NOTIFY_EMAIL=your-gmail@gmail.com
```

### 4. Gmail App Password

Gmail requires an App Password — your regular password will not work over SMTP.

1. Go to [myaccount.google.com](https://myaccount.google.com) → Security
2. Enable **2-Step Verification**
3. Search **App passwords** → generate one for Mail / Windows Computer
4. Paste the 16-character password into `SMTP_PASS`

### 5. Start Ollama and pull LLaMA 3

```bash
ollama pull llama3   # one-time download (~4 GB)
ollama serve         # keep running in background
```

### 6. Start MongoDB

MongoDB runs as a Windows service after installation. Verify with:

```bash
mongosh
```

### 7. Run the application

```bash
python main.py
```

Open **http://localhost:8000** in your browser.

Default credentials: `admin` / `admin123`

---

## Health Check

Run the built-in pipeline health check to verify all components before use:

```bash
python test.py
```

Checks: MongoDB connection, Ollama reachability, LLaMA 3 model availability, OpenCV preprocessing, EasyOCR extraction, document parser field extraction, and full end-to-end invoice pipeline.

---

## Invoice Processing Pipeline

```
Upload (PDF / JPG / PNG)
        │
        ▼
OpenCV Preprocessing
  Grayscale → Denoise → CLAHE → Deskew → Sharpen
        │
        ▼
EasyOCR Layout Extraction
  Bounding-box grouping → line reconstruction → field regex matching
  (GSTIN, invoice no., date, CGST/SGST/IGST, subtotal, total)
        │
        ▼
LLaMA 3 Enrichment  (via Ollama)
  Fills vendor name, customer name, and any fields missed by OCR
        │
        ▼
MongoDB  (invoices collection)
  Merged result + confidence scores persisted
```

---

## Reminder & Email System

The scheduler fires every day at **08:00 AM** and checks all unpaid invoices.

| Condition | Action |
|---|---|
| 7, 3, or 1 day(s) before due date | Send reminder email |
| Past due date | Mark invoice `Overdue` + send email |

Email routing:

| Invoice Type | Meaning | Email recipient |
|---|---|---|
| `outgoing` | You raised the invoice — vendor owes you | Vendor email (set in Vendors panel) |
| `incoming` | Vendor raised the invoice — you owe them | `NOTIFY_EMAIL` from `.env` |

To manually trigger a check:

```
POST /reminders/run-check
```

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login` | Login and set session cookie |
| `POST` | `/auth/logout` | Clear session cookie |

### Invoices
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload-invoice` | Upload and process invoice (OCR + LLM) |
| `GET` | `/invoices/list/{user_id}` | List all invoices |
| `GET` | `/invoice/detail/{id}` | Get single invoice detail |

### Vendors
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/vendors` | List all vendors with stats |
| `GET` | `/vendor/{id}/detail` | Vendor detail with invoice history |
| `PUT` | `/vendor/{id}/email` | Set or update vendor email |

### Bookkeeping
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/summary/{user_id}` | Income / expense / balance summary |
| `GET` | `/transactions/{user_id}` | List all transactions |
| `POST` | `/transactions/add` | Add transaction |
| `PUT` | `/transactions/update/{id}` | Update transaction |
| `DELETE` | `/transactions/delete/{id}` | Delete transaction |

### Financial Calculators
| Method | Endpoint | Inputs |
|---|---|---|
| `POST` | `/calculate/roi` | `investment`, `net_profit` |
| `POST` | `/calculate/margin` | `revenue`, `cost` |
| `POST` | `/calculate/cashflow` | `inflows`, `outflows` |
| `POST` | `/calculate/emi` | `principal`, `annual_rate`, `tenure_months` |
| `POST` | `/calculate/gst` | `amount`, `rate`, `inclusive` |

### Reminders
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/reminders/upcoming` | Invoices due within 7 days |
| `GET` | `/reminders/overdue` | All overdue invoices |
| `GET` | `/reminders/dashboard` | Combined summary with totals |
| `POST` | `/reminders/run-check` | Manually trigger daily job |

### Chat
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | AI chatbot (LLaMA 3 via Ollama) |

---

## MongoDB Collections

| Collection | Description |
|---|---|
| `invoices` | Processed invoices — OCR/LLM fields, GST breakdown, `payment_status`, confidence scores |
| `vendors` | Auto-created vendor records including optional `email` |
| `transactions` | Income and expense entries |
| `reminders` | One record per invoice per reminder threshold |

---

## Environment Variables

| Variable | Description |
|---|---|
| `MONGODB_URI` | MongoDB connection string |
| `DATABASE_NAME` | MongoDB database name |
| `ADMIN_USERNAME` | Dashboard login username |
| `ADMIN_PASSWORD` | Dashboard login password |
| `OLLAMA_URL` | Ollama API endpoint |
| `OLLAMA_MODEL` | Model name (e.g. `llama3`) |
| `UPLOAD_DIR` | Directory for uploaded invoice files |
| `SECRET_KEY` | Secret key for session signing |
| `SMTP_HOST` | SMTP server (default: `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default: `587`) |
| `SMTP_USER` | Gmail address used to send emails |
| `SMTP_PASS` | Gmail App Password (16 characters) |
| `NOTIFY_EMAIL` | Your email — receives incoming invoice reminders |

---

## License

MIT License — free to use and modify.
