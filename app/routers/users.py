from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas, database

router = APIRouter(prefix="/users", tags=["Users"])

# Dependency to get DB session
get_db = database.get_db

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user
    """
    #validation for email
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    #create user object
    new_user = models.User(username=user.username, email=user.email)

    #save to db
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.get("/{user_id}/documents", response_model=List[schemas.DocumentResponse])
def get_user_documents(user_id: int,db: Session = Depends(get_db)):
    """
    Fetch all documents belonging to a specific user.
    """
    #1. Check if user exists(optional)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, details="User not found")
    
    # 2. Fetch documents via relationship or direct query
    return db.query(models.Document).filter(models.Document.user_id == user_id).all()
