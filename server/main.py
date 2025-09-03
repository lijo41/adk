"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routes.document_routes import document_router
from routes.chat_routes import chat_router
from routes.gstr1_routes import gstr1_router
from routes.auth_routes import auth_router

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="GST Filing System API",
    description="Backend API for document processing, GSTR-1 generation, and AI chat",
    version="1.0.0"
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

@app.get("/")
async def root():
    return {"message": "GST Filing System API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
