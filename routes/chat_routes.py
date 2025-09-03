"""Chat routes for AI-powered conversations."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from usecases.chat_usecase import ChatUseCase
from models.api_requests import ChatRequest, ChatResponse
from auth.dependencies import get_current_active_user
from schemas.simplified_schemas import UserDB

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])

# Dependency injection
def get_chat_usecase() -> ChatUseCase:
    from usecases.shared_instances import chat_usecase
    return chat_usecase

@chat_router.post("/ask")
async def ask_question(
    request: ChatRequest,
    current_user: UserDB = Depends(get_current_active_user),
    usecase: ChatUseCase = Depends(get_chat_usecase)
):
    """Ask a question about documents."""
    # Input validation
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    if len(request.question) > 1000:
        raise HTTPException(status_code=400, detail="Question too long (max 1000 characters)")
    
    try:
        # Delegate to use case
        result = usecase.process_question(request.question, request.document_ids)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@chat_router.get("/documents/{document_id}/summary")
async def get_document_summary(
    document_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    usecase: ChatUseCase = Depends(get_chat_usecase)
):
    """Get AI-generated summary for a document."""
    # Input validation
    if not document_id or not document_id.strip():
        raise HTTPException(status_code=400, detail="Invalid document ID")
    
    try:
        result = usecase.get_document_summary(document_id)
        if not result:
            raise HTTPException(status_code=404, detail="Document not found")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
