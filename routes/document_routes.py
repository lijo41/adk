"""Document processing routes."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from auth.dependencies import get_current_active_user
from schemas.simplified_schemas import UserDB
import uuid

document_router = APIRouter(prefix="/api/documents", tags=["documents"])

@document_router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Upload and process document in-memory only."""
    try:
        # Read file content
        content = await file.read()
        
        # Simple in-memory processing - no persistence
        document_id = str(uuid.uuid4())
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "status": "processed",
            "content_length": len(content),
            "message": "Document processed in-memory (no storage)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@document_router.get("/")
async def list_documents(
    current_user: UserDB = Depends(get_current_active_user)
):
    """List documents - no storage, returns empty list."""
    return {"documents": [], "message": "No document storage - processing in-memory only"}

@document_router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Get document - no storage available."""
    raise HTTPException(status_code=404, detail="Document not found - no storage enabled")

@document_router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Delete document - no storage available."""
    raise HTTPException(status_code=404, detail="Document not found - no storage enabled")
