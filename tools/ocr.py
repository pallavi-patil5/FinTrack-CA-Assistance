import pytesseract
from PIL import Image
from config.settings import TESSERACT_PATH

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def extract_text(file_path: str):
    try:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)
    except Exception as e:
        raise RuntimeError(f"OCR failed: {str(e)}")