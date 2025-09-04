"""Document processing routes."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from auth.dependencies import get_current_active_user
from schemas.simplified_schemas import UserDB
from usecases.shared_instances import get_document_processing_agent
import uuid
import tempfile
import os

document_router = APIRouter(prefix="/api/documents", tags=["documents"])

@document_router.post("/upload")
async def upload_documents(
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_active_user)
):
    """Upload and process single document with parsing and chunking."""
    try:
        # Get document processing agent
        doc_agent = get_document_processing_agent()
        
        # Read file content
        content = await file.read()
        
        # Create temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Use document processing agent to parse and chunk
            from agents.document_processing_agent import parse_document_content, parse_document_content_with_filename, document_store
            
            # Parse document content with original filename
            parse_result = parse_document_content_with_filename(temp_file_path, file.filename)
            
            if parse_result.startswith("Error"):
                raise HTTPException(status_code=400, detail=parse_result)
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Get chunks for this document
            chunks = document_store["chunks"].get(file.filename, [])
            
            return {
                "document_id": document_id,
                "filename": file.filename,
                "status": "processed",
                "content_length": len(content),
                "content_type": file.content_type,
                "chunks_created": len(chunks),
                "parse_result": parse_result
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
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
