import io
from PIL import Image
import pytesseract
from pypdf import PdfReader

def extract_text_with_ocr_fallback(pdf_path):
    reader = PdfReader(pdf_path)
    text_pages = []
    
    for page_idx, page in enumerate(reader.pages):
        txt = page.extract_text() or ""
        if txt.strip():
            text_pages.append(txt.strip())
        else:
            # Fallback: extract images from scanned PDF page
            try:
                for img_obj in page.images:
                    img_bytes = img_obj.data
                    img = Image.open(io.BytesIO(img_bytes))
                    ocr_txt = pytesseract.image_to_string(img)
                    if ocr_txt and ocr_txt.strip():
                        text_pages.append(ocr_txt.strip())
            except Exception as e:
                print(f"Page {page_idx} image OCR error: {e}")

    return "\n\n".join(text_pages).strip()
