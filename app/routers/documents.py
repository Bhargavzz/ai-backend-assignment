from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import models, schemas, database

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