import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DATABASE_NAME", "EDAI6")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

invoices_col = db["invoices"]
vendors_col = db["vendors"]
transactions_col = db["transactions"]
