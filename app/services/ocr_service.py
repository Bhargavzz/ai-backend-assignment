import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import io
import shutil
import os
from dotenv import load_dotenv

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
    """Converts PDF -> Images -> Text."""
    # Ensure Poppler path is set
    if not POPPLER_PATH or not os.path.exists(POPPLER_PATH):
        raise EnvironmentError("Poppler path not set or invalid. Please set POPPLER_PATH in .env.")
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=300, poppler_path=POPPLER_PATH)
        full_text = []
        for i, page in enumerate(pages):
            text = pytesseract.image_to_string(page)
            full_text.append(f"--- Page {i+1} ---\n{text}")
        
        return "\n\n".join(full_text)
        
    except Exception as e:
        if "poppler" in str(e).lower():
            raise EnvironmentError("Error with Poppler. Ensure Poppler is installed and POPPLER_PATH is correct.")
        raise ValueError(f"Error processing PDF: {str(e)}")
    



