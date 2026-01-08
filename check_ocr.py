# check_ocr.py
import pytesseract
import shutil

# IF Tesseract is not in your PATH, you might need to uncomment this line:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

print("Checking Tesseract...")
if shutil.which("tesseract") or pytesseract.pytesseract.tesseract_cmd:
    print("✅ Tesseract found!")
    try:
        print(f"Version: {pytesseract.get_tesseract_version()}")
    except:
        print("⚠️ Found binary but could not get version. Check path.")
else:
    print("❌ Tesseract NOT found. Please install it or set the path in code.")