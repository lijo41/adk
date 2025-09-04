"""Main FastAPI application."""

from database.database import get_db, engine
from schemas.simplified_schemas import Base
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from routes.document_routes import document_router
from routes.chat_routes import chat_router
from routes.gstr1_routes import gstr1_router
from routes.auth_routes import auth_router
from routes.filing_routes import filing_router
from routes.reports_routes import reports_router
from routes.cleanup_routes import router as cleanup_router

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    from sqlalchemy import text
    from schemas.simplified_schemas import UserDB
    
    # Get all table names except users table
    with engine.connect() as conn:
        # Get existing table names
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        existing_tables = [row[0] for row in result.fetchall()]
        
        # Drop all tables except users
        tables_to_drop = [table for table in existing_tables if table != 'users' and table != 'sqlite_sequence']
        
        for table_name in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                print(f"Dropped table: {table_name}")
            except Exception as e:
                print(f"Error dropping table {table_name}: {e}")
        
        conn.commit()
    
    # Create all tables (this will create new tables but preserve users table)
    Base.metadata.create_all(bind=engine)
    print("Database refreshed - users table preserved, other tables recreated")
    yield
    # Shutdown (if needed)
    print("Application shutting down")

# Create FastAPI app
app = FastAPI(
    title="GST Filing System API",
    description="Backend API for document processing, GSTR-1 generation, and AI chat",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(document_router)
app.include_router(chat_router)
app.include_router(gstr1_router)
app.include_router(filing_router)
app.include_router(reports_router)
app.include_router(cleanup_router)

@app.get("/")
async def root():
    return {"message": "GST Filing System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
