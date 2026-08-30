import os
import pypdf

def inspect_pdf():
    pdf_path = r'C:\Users\a\OneDrive\Desktop\NotesEnhancer\backend\media\syllabi\SocialScience_SecP1IX_2026-27.pdf'
    reader = pypdf.PdfReader(pdf_path)
    print(f"Total pages: {len(reader.pages)}")

    with open('extracted_social_science_raw.txt', 'w', encoding='utf-8') as out:
        for idx, page in enumerate(reader.pages, 1):
            txt = page.extract_text() or ""
            out.write(f"\n==================== PAGE {idx} ====================\n")
            out.write(txt)
            print(f"Page {idx}: {len(txt)} chars extracted.")

if __name__ == "__main__":
    inspect_pdf()
