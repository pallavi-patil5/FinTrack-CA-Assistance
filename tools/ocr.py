import pytesseract
from PIL import Image
from config.settings import TESSERACT_PATH
import os

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def extract_text(file_path: str):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            try:
                from pdf2image import convert_from_path
                pages = convert_from_path(file_path, dpi=200)
                return "\n".join(pytesseract.image_to_string(p) for p in pages)
            except ImportError:
                raise RuntimeError("PDF upload requires pdf2image. Run: pip install pdf2image")
        else:
            img = Image.open(file_path)
            return pytesseract.image_to_string(img)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"OCR failed: {str(e)}")