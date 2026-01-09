from pydantic import BaseModel, EmailStr, Field, validator
from typing import List,Optional
from datetime import datetime

# USER SCHEMAS

class UserBase(BaseModel):
    """Shared properties for reading and writing"""
    # Min 3, max 50 chars, alphanumeric + underscore only (prevents XSS, ensures reasonable length)
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr  # Pydantic validates email format automatically

class UserCreate(UserBase):
    """Properties needed to CREATE a user(Input)"""
    pass

class UserResponse(UserBase):
    """Properties returned to the client(Output)"""
    id: int
    created_at: datetime

    class Config:
        # Required for Pydantic to serialize SQLAlchemy ORM models
        from_attributes = True


# DOCUMENT SCHEMAS
class DocumentBase(BaseModel):
    # Title: 1-200 chars (prevents empty/massive titles)
    title: str = Field(..., min_length=1, max_length=200)
    # Content: max 50KB (prevents DB overload from huge text blobs)
    content: Optional[str] = Field(None, max_length=50000)

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

# OCR SCHEMA
class OCRResponse(BaseModel):
    """Schema for the OCR extraction result"""
    filename: str
    content_type: str
    extracted_text: str


# VECTOR SEARCH SCHEMAS

class IndexRequest(BaseModel):
    """Request to index documents"""
    document_ids: List[int]

class IndexResponse(BaseModel):
    """Response after indexing"""
    indexed_count: int
    failed_ids: List[int] = []
    message: str

class SearchRequest(BaseModel):
    """Search request"""
    query: str
    top_k: int = 5  

class SearchResult(BaseModel):
    """Single search result"""
    document_id: int
    title: str
    content: str
    similarity_score: float

class SearchResponse(BaseModel):
    """Search Response"""
    query: str
    results: List[SearchResult]
    total_results: int




    