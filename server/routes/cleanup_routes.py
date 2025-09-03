"""Cleanup routes for clearing user session data during logout."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from auth.dependencies import get_current_user
from schemas.simplified_schemas import UserDB as User
from usecases.document_usecase import DocumentUseCase

router = APIRouter(prefix="/cleanup", tags=["cleanup"])

class ClearChunksRequest(BaseModel):
    document_ids: List[str]

@router.post("/session")
async def clear_user_session_data(
    current_user: User = Depends(get_current_user),
    document_usecase: DocumentUseCase = Depends()
) -> Dict[str, Any]:
    """
    Clear all user session data including document chunks from memory.
    Preserves user account data but removes all documents and chunks.
    """
    try:
        # Get all user documents
        user_documents = document_usecase.get_all_documents()
        
        # Clear all documents and chunks from memory
        cleared_documents = 0
        cleared_chunks = 0
        
        for doc in user_documents:
            # Count chunks before clearing
            chunks = document_usecase.get_chunks(doc.id)
            cleared_chunks += len(chunks)
            
            # Delete document (this also clears associated chunks)
            if document_usecase.delete_document(doc.id):
                cleared_documents += 1
        
        return {
            "message": f"Session data cleared successfully. Removed {cleared_documents} documents and {cleared_chunks} chunks.",
            "cleared_documents": cleared_documents,
            "cleared_chunks": cleared_chunks
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear session data: {str(e)}"
        )

@router.post("/chunks")
async def clear_document_chunks(
    request: ClearChunksRequest,
    current_user: User = Depends(get_current_user),
    document_usecase: DocumentUseCase = Depends()
) -> Dict[str, Any]:
    """
    Clear specific document chunks by document IDs.
    """
    try:
        cleared_count = 0
        
        for doc_id in request.document_ids:
            # Get chunks count before clearing
            chunks = document_usecase.get_chunks(doc_id)
            if chunks:
                cleared_count += len(chunks)
                # Clear chunks for this document
                document_usecase._chunks[doc_id] = []
        
        return {
            "message": f"Cleared {cleared_count} chunks for {len(request.document_ids)} documents.",
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear document chunks: {str(e)}"
        )

@router.delete("/documents")
async def clear_all_user_documents(
    current_user: User = Depends(get_current_user),
    document_usecase: DocumentUseCase = Depends()
) -> Dict[str, Any]:
    """
    Clear all documents and chunks for current user.
    """
    try:
        # Get all user documents
        user_documents = document_usecase.get_all_documents()
        
        cleared_documents = 0
        cleared_chunks = 0
        
        for doc in user_documents:
            # Count chunks before clearing
            chunks = document_usecase.get_chunks(doc.id)
            cleared_chunks += len(chunks)
            
            # Delete document and its chunks
            if document_usecase.delete_document(doc.id):
                cleared_documents += 1
        
        return {
            "message": f"All user documents cleared. Removed {cleared_documents} documents and {cleared_chunks} chunks.",
            "cleared_documents": cleared_documents,
            "cleared_chunks": cleared_chunks
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear user documents: {str(e)}"
        )
