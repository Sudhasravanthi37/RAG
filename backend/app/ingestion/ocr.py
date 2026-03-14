import os
import cv2
import pytesseract
import pdfplumber
from pdf2image import convert_from_path
from docx import Document

# Windows: uncomment and set path if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_image(path: str) -> str:
    img = cv2.imread(path)
    if img is None:
        return ""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return pytesseract.image_to_string(gray).strip()

def _is_scanned(path: str) -> bool:
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                return False
    return True

def extract_text_from_pdf(path: str) -> str:
    if not _is_scanned(path):
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text.strip()
    images = convert_from_path(path)
    return "\n".join(pytesseract.image_to_string(img) for img in images).strip()

def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs).strip()

def extract_text_from_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()

def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in {".png", ".jpg", ".jpeg"}:
        return extract_text_from_image(path)
    if ext == ".pdf":
        return extract_text_from_pdf(path)
    if ext == ".docx":
        return extract_text_from_docx(path)
    if ext == ".txt":
        return extract_text_from_txt(path)
    raise ValueError(f"Unsupported file type: {ext}")
