from fastapi import FastAPI
from app.database import engine, Base
from app.routers import users, documents

# create tables
# this ensures tables exist when the app starts
Base.metadata.create_all(bind=engine)

# initialize app
app = FastAPI(title="Document Management API")

#include routers
app.include_router(users.router)
app.include_router(documents.router)

@app.get("/")
def read_root():
    return {
        "message":"Welcome to the Document Management API"
    }