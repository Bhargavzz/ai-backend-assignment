import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import io
import shutil
import os
from dotenv import load_dotenv
import pypdf

load_dotenv()


#Configuration
TESSERACT_PATH=os.getenv("TESSERACT_PATH") 
POPPLER_PATH=os.getenv("POPPLER_PATH")

#Auto-configure Tesseract path if not set
if TESSERACT_PATH and os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
    # If not in .env, check if its in  System PATH
    if not shutil.which("tesseract"):
        raise EnvironmentError("Tesseract executable not found. Please set TESSERACT_PATH in .env or add Tesseract to system PATH.")
    

def process_image(image_bytes: bytes) -> str:
    """Reads text from an image files(png,jpg) bytes"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")
    

def process_pdf(pdf_bytes: bytes) -> str:
    """
    Smart Processing (Fixed for short text):
    1. Checks if the PDF has ANY selectable text.
    2. If yes -> Returns text instantly (No OCR).
    3. If no (or only whitespace) -> Runs standard OCR.
    """
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = pypdf.PdfReader(pdf_file)
        full_text = []
        has_actual_text = False

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                full_text.append(f"--- Page {i+1} ---\n{text.strip()}")
                
                if text.strip():
                    has_actual_text = True

        # If we fond any real text chars, return it directly
        if has_actual_text:
            return "\n\n".join(full_text)
    except Exception as e:
        #fallback to ocr
        pass

    #Fallback to OCR

    # Ensure Poppler path is set
    if not POPPLER_PATH or not os.path.exists(POPPLER_PATH):
        raise EnvironmentError("Poppler path not set or invalid. Please set POPPLER_PATH in .env.")
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=300, poppler_path=POPPLER_PATH)
        ocr_text = []
        for i, page in enumerate(pages):
            text = pytesseract.image_to_string(page)
            ocr_text.append(f"--- Page {i+1} ---\n{text}")
        
        return "\n\n".join(ocr_text)
        
    except Exception as e:
        if "poppler" in str(e).lower():
            raise EnvironmentError("Error with Poppler. Ensure Poppler is installed and POPPLER_PATH is correct.")
        raise ValueError(f"Error processing PDF: {str(e)}")
    



