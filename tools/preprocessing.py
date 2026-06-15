"""
tools/preprocessing.py
----------------------
OpenCV-based invoice image preprocessing pipeline.
Runs before OCR to maximise text-extraction accuracy.

Supported formats: PNG, JPG, JPEG, PDF
"""

import os
import tempfile
import math

import cv2
import numpy as np
from PIL import Image, ImageEnhance


# ---------------------------------------------------------------------------
# Helper: deskew
# ---------------------------------------------------------------------------

def deskew_image(gray: np.ndarray) -> np.ndarray:
    """Detect and correct skew angle using Hough line transform."""
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, math.pi / 180, threshold=80,
                            minLineLength=50, maxLineGap=10)
    if lines is None:
        return gray

    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 != x1:
            angles.append(math.degrees(math.atan2(y2 - y1, x2 - x1)))

    if not angles:
        return gray

    median_angle = np.median(angles)
    # Only correct if skew is meaningful (> 0.5°) and not extreme (> 45°)
    if abs(median_angle) < 0.5 or abs(median_angle) > 45:
        return gray

    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


# ---------------------------------------------------------------------------
# Helper: remove borders
# ---------------------------------------------------------------------------

def remove_borders(binary: np.ndarray) -> np.ndarray:
    """Crop away solid black/white border bands using contour bounding box."""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return binary

    all_pts = np.vstack(contours)
    x, y, w, h = cv2.boundingRect(all_pts)

    # Add a 5-pixel safety margin so we don't clip text at edges
    margin = 5
    x = max(0, x - margin)
    y = max(0, y - margin)
    w = min(binary.shape[1] - x, w + 2 * margin)
    h = min(binary.shape[0] - y, h + 2 * margin)

    return binary[y:y + h, x:x + w]


# ---------------------------------------------------------------------------
# Helper: enhance contrast
# ---------------------------------------------------------------------------

def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalisation)."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


# ---------------------------------------------------------------------------
# Helper: confidence score
# ---------------------------------------------------------------------------

def compute_confidence(binary: np.ndarray) -> float:
    """
    Estimate image quality as a confidence score in [0, 1].

    Heuristic: a well-preprocessed invoice should have ~10–50 % white pixels
    (text on white background after thresholding inverts background to white).
    Score is penalised when the white-pixel ratio is outside that sweet spot.
    """
    total = binary.size
    if total == 0:
        return 0.0

    white_ratio = float(np.sum(binary == 255)) / total

    # Ideal range: 50–90 % white (mostly background, some dark text)
    if 0.50 <= white_ratio <= 0.90:
        score = 1.0
    elif white_ratio < 0.50:
        score = white_ratio / 0.50          # linearly worse toward 0
    else:
        score = (1.0 - white_ratio) / 0.10  # linearly worse above 90 %

    return round(min(max(score, 0.0), 1.0), 4)


# ---------------------------------------------------------------------------
# PDF → image helper
# ---------------------------------------------------------------------------

def _pdf_to_images(file_path: str) -> list[str]:
    """Convert each PDF page to a temporary PNG using PyMuPDF (no Poppler needed)."""
    import fitz  # PyMuPDF
    doc = fitz.open(file_path)
    tmp_paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=300)  # 300 dpi for better OCR accuracy
        with tempfile.NamedTemporaryFile(
            suffix=f"_page{i}.png", delete=False, prefix="sarthi_preproc_"
        ) as tmp:
            tmp_name = tmp.name
        pix.save(tmp_name)
        tmp_paths.append(tmp_name)
    doc.close()
    return tmp_paths


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def preprocess_image(image_path: str) -> dict:
    """
    Full preprocessing pipeline for an invoice image.

    Steps
    -----
    1. Load image (supports PNG / JPG / JPEG directly; PDF via pdf2image)
    2. Grayscale conversion
    3. Gaussian blur  – noise removal
    4. CLAHE          – contrast enhancement
    5. Deskew         – skew correction
    6. Adaptive threshold – binarisation
    7. Border removal
    8. Resize          – normalise to 1200 px wide for Tesseract

    Returns
    -------
    dict with keys:
        output_path  : str   – path to cleaned image
        confidence   : float – quality score in [0, 1]
        skipped_pdf  : bool  – True when input was a multi-page PDF
                               (only first page preprocessed automatically;
                                caller may loop over pdf_pages)
        pdf_pages    : list  – temp PNG paths for each PDF page (may be empty)
    """
    ext = os.path.splitext(image_path)[1].lower()

    # ------------------------------------------------------------------
    # PDF: convert pages then preprocess each; return first page result
    # ------------------------------------------------------------------
    if ext == ".pdf":
        page_paths = _pdf_to_images(image_path)
        results = [_process_single(p) for p in page_paths]
        # Return best-confidence page as primary result
        best = max(results, key=lambda r: r["confidence"])
        best["pdf_pages"] = [r["output_path"] for r in results]
        best["skipped_pdf"] = len(page_paths) > 1
        return best

    return _process_single(image_path)


def _process_single(image_path: str) -> dict:
    """Run the full pipeline on one image file."""
    # 1. Load
    img = cv2.imread(image_path)
    if img is None:
        with Image.open(image_path) as pil_img:
            img = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

    # 2. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 3. Upscale small images — EasyOCR needs at least ~1600px wide for dense invoices
    h, w = gray.shape
    if w < 1600:
        scale = 1600 / w
        gray = cv2.resize(gray, (1600, int(h * scale)), interpolation=cv2.INTER_LANCZOS4)

    # 4. Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # 5. Contrast enhancement (CLAHE)
    gray = enhance_contrast(gray)

    # 6. Deskew
    gray = deskew_image(gray)

    # 7. Sharpen — helps EasyOCR on blurry scans
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, kernel)

    # Confidence score on grayscale (no binarisation — EasyOCR prefers grayscale)
    confidence = compute_confidence(
        cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    )

    with tempfile.NamedTemporaryFile(
        suffix=".png", delete=False, prefix="sarthi_clean_"
    ) as tmp:
        tmp_name = tmp.name
    cv2.imwrite(tmp_name, gray)

    return {
        "output_path": tmp_name,
        "confidence": confidence,
        "pdf_pages": [],
        "skipped_pdf": False,
    }
