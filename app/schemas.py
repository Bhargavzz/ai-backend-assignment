from pydantic import BaseModel, EmailStr
from typing import List,Optional
from datetime import datetime

# USER SCHEMAS

class UserBase(BaseModel):
    """Shared properties for reading and writing"""
    username: str
    email: EmailStr #pydantic automatically validate if this is a real email format

class UserCreate(UserBase):
    """Properties needed to CREATE a user(Input)"""
    pass

class UserResponse(UserBase):
    """Properties returned to the client(Output)"""
    id: int
    created_at: datetime

    #This tells Pydantic to read data from sqlalchemy models(which are objects), not just standard dictionaries.



# DOCUMENT SCHEMAS
class DocumentBase(BaseModel):
    title: str
    content: Optional[str] = None #Content is optional when creating (might be uploaded later)

class DocumentCreate(DocumentBase):
    """Input Schema"""
    user_id: int #owner's id

class DocumentResponse(DocumentBase):
    """Output Schema"""
    id: int
    created_at: datetime

    #We don't return user_id here typically, but we could if needed.

    class Config:
        from_attributes = True


    