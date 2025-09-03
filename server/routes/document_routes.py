"""Document API routes."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
from dotenv import load_dotenv

from shared_instances import document_usecase, chat_usecase

# Load environment
load_dotenv()

document_router = APIRouter(prefix="/api/documents", tags=["documents"])


@document_router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a single document."""
    try:
        # Read file content
        content = await file.read()
        
        # Process document
        document = document_usecase.upload_document(
            filename=file.filename,
            file_content=content,
            file_type=file.content_type or file.filename.split('.')[-1]
        )
        
        if document.status.value == "error":
            raise HTTPException(status_code=400, detail=document.error_message)
        
        # Create chunks and summary
        chunks = document_usecase.create_chunks(document)
        summary = chat_usecase.create_document_summary(document)
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "status": document.status.value,
            "content_length": len(document.content),
            "chunks_count": len(chunks),
            "summary": summary.summary[:200] + "..." if len(summary.summary) > 200 else summary.summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@document_router.post("/upload-multiple")
async def upload_multiple_documents(files: List[UploadFile] = File(...)):
    """Upload multiple documents."""
    results = []
    
    for file in files:
        try:
            content = await file.read()
            document = document_usecase.upload_document(
                filename=file.filename,
                file_content=content,
                file_type=file.content_type or file.filename.split('.')[-1]
            )
            
            if document.status.value == "processed":
                chunks = document_usecase.create_chunks(document)
                summary = chat_usecase.create_document_summary(document)
                
                results.append({
                    "document_id": document.id,
                    "filename": document.filename,
                    "status": "success",
                    "content_length": len(document.content),
                    "chunks_count": len(chunks)
                })
            else:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": document.error_message
                })
                
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error", 
                "error": str(e)
            })
    
    return {"results": results}


@document_router.get("/list")
async def list_documents():
    """List all uploaded documents."""
    documents = document_usecase.list_documents()
    return {
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type.value,
                "status": doc.status.value,
                "upload_time": doc.upload_time.isoformat(),
                "file_size": doc.file_size
            }
            for doc in documents
        ]
    }


@document_router.get("/{document_id}")
async def get_document(document_id: str):
    """Get document details."""
    document = document_usecase.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "file_type": document.file_type.value,
        "status": document.status.value,
        "upload_time": document.upload_time.isoformat(),
        "processed_time": document.processed_time.isoformat() if document.processed_time else None,
        "content_preview": document.content[:500] + "..." if len(document.content) > 500 else document.content
    }


@document_router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document."""
    success = document_usecase.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}
