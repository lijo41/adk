"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routes.document_routes import document_router
from routes.gstr1_routes import gstr1_router
from routes.chat_routes import chat_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="ADK Document Processing API",
    description="Backend API for document processing, GSTR-1 generation, and AI chat",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(document_router)
app.include_router(gstr1_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ADK Document Processing API",
        "version": "1.0.0",
        "endpoints": {
            "documents": "/api/documents",
            "gstr1": "/api/gstr1", 
            "chat": "/api/chat"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
