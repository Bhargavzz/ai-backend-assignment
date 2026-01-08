import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db

# Set testing flag BEFORE importing app/models
os.environ["TESTING"] = "1"

from app import models  # Import models so Base.metadata knows about them
from app.main import app

# Use in-memory SQLite for tests (fast, isolated, no cleanup needed)
# Important: poolclass=StaticPool with check_same_thread=False
# ensures all connections share the SAME in-memory database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    poolclass=StaticPool  # CRITICAL: ensures single shared connection for :memory:
)

# Enable foreign key constraints in SQLite (off by default)
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def client():
    """
    TestClient with test database.
    Each test gets a fresh client with isolated database.
    """
    # Create tables for this test
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        # Create session for this test
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    # Drop tables after test
    Base.metadata.drop_all(bind=engine)
