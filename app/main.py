from fastapi import FastAPI
from app.database import engine, Base
from app.routers import users, documents, search, ai
import os

# Only create tables if not in test environment
# Tests will create their own tables with their own engine
if os.getenv("TESTING") != "1":
    Base.metadata.create_all(bind=engine)

# initialize app
app = FastAPI(title="Document Management API")

#include routers
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(ai.router)

@app.get("/")
def read_root():
    return {
        "message":"Welcome to the Document Management API"
    }