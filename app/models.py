from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

class User(Base):
    __tablename__="users"

    #Columns
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True , index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    # Use lambda so timestamp is generated per-record, not at class definition
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    #Relationships
    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")


class Document(Base):
    __tablename__="documents"

    #Columns
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100),nullable=False)
    content = Column(Text, nullable=True)
    # Use lambda for per-record timestamp generation
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    #Foreign Key
    user_id = Column(Integer,ForeignKey("users.id"),nullable=False)

    #Relationships
    owner = relationship("User", back_populates="documents")



