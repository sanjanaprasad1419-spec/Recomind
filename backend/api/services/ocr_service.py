import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)

def process_note_ocr(file_path: str, file_type: str = "") -> str:
    """
    Extracts text from uploaded study notes (PDF, DOCX, JPG, JPEG, PNG).
    Supports multi-page PDFs, Word documents, and Image OCR via pytesseract.
    """
    if isinstance(file_path, int): # If a note ID was passed directly
        from api.models import Note
        try:
            note = Note.objects.get(id=file_path)
            file_path = note.uploaded_file.path
            file_type = note.file_type
        except Exception:
            return "Study Notes Document"

    if not file_type and isinstance(file_path, str):
        file_type = os.path.splitext(file_path)[1].lower().replace('.', '')

    ext = file_type.lower().replace('.', '')
    extracted_text = ""

    if ext == 'pdf':
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            page_texts = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt and txt.strip():
                    page_texts.append(txt.strip())
            extracted_text = "\n\n".join(page_texts)
        except Exception as e:
            logger.error(f"PDF note extraction error: {e}")

    elif ext == 'docx':
        try:
            import docx
            doc = docx.Document(file_path)
            full_text = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            extracted_text = "\n".join(full_text)
        except Exception as e:
            logger.error(f"DOCX note extraction error: {e}")

    elif ext in ['jpg', 'jpeg', 'png']:
        try:
            import pytesseract
            img = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(img)
        except Exception as e:
            logger.warning(f"Image OCR note extraction fallback: {e}")
            extracted_text = f"Image Note Document: {os.path.basename(file_path)}"

    # Fallback to direct file read if empty
    if not extracted_text or not extracted_text.strip():
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                extracted_text = f.read()
        except Exception:
            extracted_text = f"Study Notes Document: {os.path.basename(file_path)}"

    return extracted_text.strip()
