from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas, database

router = APIRouter(prefix="/documents",tags=["Documents"])
get_db=database.get_db

# FIX: Changed response_model to DocumentResponse so we return the ID
@router.post("/", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(doc: schemas.DocumentCreate, db: Session = Depends(get_db)):
    """
    Create a new document for an existing user

    """
    #Validation : Ensure user_id belongs to a real user
    user = db.query(models.User).filter(models.User.id == doc.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #create document object

    new_doc = models.Document(
        title=doc.title,
        content=doc.content,
        user_id=doc.user_id
    )
    
    #save to db
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return new_doc