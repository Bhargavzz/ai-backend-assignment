# Phase 2: OCR Document Ingestion

## Overview
This phase implements optical character recognition (OCR) capabilities to extract text from uploaded PDF and image files. The service uses Tesseract OCR for text extraction and Poppler for PDF processing.

## Features Implemented

### OCR Upload Endpoint
**`POST /documents/upload`**

Accepts file uploads (PDF, PNG, JPEG) and extracts text using OCR.

**Request:**
- **Content-Type**: `multipart/form-data`
- **Parameter**: `file` (binary)
- **Supported formats**: PDF, PNG, JPEG
- **Max file size**: 10 MB

**Response:**
```json
{
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "extracted_text": "Extracted text content..."
}
```

**Status Codes:**
- `200` - Success
- `400` - Unsupported file type
- `413` - File size exceeds limit
- `500` - OCR processing error

## Architecture

### Components
```
app/
├── routers/
│   └── documents.py       # Upload endpoint with validation
└── services/
    └── ocr_service.py     # OCR processing logic
```

### OCR Service Functions
- **`process_image(image_bytes)`** - Extracts text from PNG/JPEG images
- **`process_pdf(pdf_bytes)`** - Converts PDF pages to images, then extracts text

## Setup Instructions

### 1. Install Tesseract OCR

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to `C:\Program Files\Tesseract-OCR\`
3. Add to PATH or set in `.env`

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 2. Install Poppler (for PDF processing)

**Windows:**
1. Download from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to `C:\Program Files\poppler\`
3. Set path in `.env`

**Linux:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

### 3. Configure Environment Variables

Create/update `.env` file:
```env
# Tesseract Path (Windows only, optional if in PATH)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# Poppler Path (Required for PDF processing)
POPPLER_PATH=C:\Program Files\poppler\Library\bin
```

### 4. Install Python Dependencies

```bash
pip install pytesseract pillow pdf2image
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

## Usage Examples

### Upload Image (cURL)
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.png"
```

### Upload PDF (cURL)
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Python Example
```python
import requests

url = "http://localhost:8000/documents/upload"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)

print(response.json()["extracted_text"])
```

## Validation & Error Handling

### File Type Validation
Only allows:
- `application/pdf`
- `image/png`
- `image/jpeg`

### File Size Limit
- Maximum: 10 MB
- Returns `413 Payload Too Large` if exceeded

### Error Responses
All errors return JSON with detail message:
```json
{
  "detail": "Error description"
}
```

## Technical Details

### PDF Processing Flow
1. PDF bytes → `convert_from_bytes()` (via Poppler)
2. Each page → PIL Image
3. Image → Tesseract OCR → Text
4. Combine all pages with page markers

### Image Processing Flow
1. Image bytes → PIL Image
2. Image → Tesseract OCR → Text

### Performance Considerations
- DPI set to 300 for optimal OCR accuracy
- Multi-page PDFs processed sequentially
- Each page marked with `--- Page N ---`

## Troubleshooting

### "Tesseract executable not found"
**Solution:**
- Verify Tesseract is installed
- Set `TESSERACT_PATH` in `.env`
- Or add Tesseract to system PATH

**Test Tesseract:**
```bash
tesseract --version
```

### "Poppler path not set or invalid"
**Solution:**
- Verify Poppler is installed
- Set correct `POPPLER_PATH` in `.env`
- Path should point to the `bin` directory

**Test Poppler:**
```bash
# Windows
"C:\Program Files\poppler\Library\bin\pdfinfo.exe" -v

# Linux/Mac
pdfinfo -v
```

### Poor OCR Accuracy
**Possible causes:**
- Low image quality/resolution
- Non-standard fonts
- Handwritten text (not supported)

**Solutions:**
- Use higher resolution images (300+ DPI)
- Ensure good contrast and lighting
- Use clear, printed text

### PDF Processing Slow
**Explanation:**
- High-resolution conversion (300 DPI) for accuracy
- Sequential page processing

**Optimization:**
- Reduce DPI if speed is priority (change in `ocr_service.py`)
- Consider async processing for large files

## Testing

### Manual Testing
1. Start server: `uvicorn app.main:app --reload`
2. Visit: http://localhost:8000/docs
3. Use Swagger UI to test `/documents/upload`

### Test Files
Use the assignment PDF or create test files:
- Simple text image
- Multi-page PDF
- Mixed content document

## Dependencies

```txt
pytesseract    # Tesseract Python wrapper
Pillow          # Image processing
pdf2image       # PDF to image conversion
python-multipart  # File upload support
```




