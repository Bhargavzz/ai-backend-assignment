from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models, schemas, database
from app.services import ocr_service

router = APIRouter(prefix="/documents",tags=["Documents"])
get_db=database.get_db

@router.post("/", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(doc: schemas.DocumentCreate, db: Session = Depends(get_db)):
    """
    Create a new document for an existing user
    """
    # Create document object
    new_doc = models.Document(
        title=doc.title,
        content=doc.content,
        user_id=doc.user_id
    )
    
    # Let FK constraint validate user existence (avoids extra DB query)
    try:
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
    except IntegrityError:
        db.rollback()
        # FK constraint failed = user_id doesn't exist
        raise HTTPException(status_code=404, detail="User not found")

    return new_doc

@router.post("/upload",response_model=schemas.OCRResponse, status_code=status.HTTP_200_OK)
async def upload_document(
    file : UploadFile = File(...),
    title : str = Form(...),  #Title via Form
    user_id : int = Form(...), #User ID via Form
    db : Session = Depends(get_db) #dependency to get DB session
    ):
    """
    Upload a file (PDF or Image) and extract text using OCR.
    """
    # Validation check for file type
    if file.content_type not in ["application/pdf", "image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF and images are allowed.")
    
    # Validation check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check file size (limit to 10 MB)
    content = await file.read()

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit.") #413 Payload Too Large
    
    try:
        if file.content_type == "application/pdf":
            extracted_text = ocr_service.process_pdf(content)
        else:
            extracted_text = ocr_service.process_image(content)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        # Log the actual error for debugging
        print(f"OCR Error: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")


    # Save to database
    new_doc = models.Document(
        title=title,
        content=extracted_text, #retrieved via OCR
        user_id=user_id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # Return OCR response
    return {
        "document_id": new_doc.id,
        "filename": file.filename,
        "content_type": file.content_type,
        "extracted_text": extracted_text
    }

