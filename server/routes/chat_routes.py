"""Chat API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

from shared_instances import chat_usecase, document_usecase

# Load environment
load_dotenv()

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    document_ids: List[str] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    context_count: int


@chat_router.post("/ask")
async def ask_question(request: ChatRequest) -> ChatResponse:
    """Ask a question about uploaded documents."""
    try:
        if not request.document_ids:
            # Get all available documents if none specified
            documents = document_usecase.list_documents()
            document_ids = [doc.id for doc in documents]
        else:
            document_ids = request.document_ids
        
        if not document_ids:
            raise HTTPException(status_code=400, detail="No documents available")
        
        # Extract contexts from each document
        contexts = []
        sources = []
        
        for doc_id in document_ids:
            document = document_usecase.get_document(doc_id)
            if not document:
                continue
            
            # Get document chunks from storage
            chunks = document_usecase.get_chunks(doc_id)
            if not chunks:
                # Create chunks if they don't exist
                chunks = document_usecase.create_chunks(document)
            
            # Debug: Print chunk info for chat
            print(f"Chat - Document {document.filename}: {len(chunks)} chunks found")
            
            # Extract context for this query
            context = chat_usecase.extract_context_for_query(
                request.question, document, chunks
            )
            
            if context.relevance_score > 0:
                contexts.append(context)
                sources.append({
                    "document_id": document.id,
                    "filename": document.filename,
                    "relevance_score": context.relevance_score,
                    "chunks_used": len(context.relevant_chunks)
                })
        
        # Generate answer
        answer = chat_usecase.answer_question(request.question, contexts)
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            context_count=len(contexts)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.get("/documents")
async def get_available_documents():
    """Get list of documents available for chat."""
    try:
        documents = document_usecase.list_documents()
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status.value,
                    "upload_time": doc.upload_time.isoformat()
                }
                for doc in documents
                if doc.status.value == "processed"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/summarize/{document_id}")
async def summarize_document(document_id: str):
    """Generate summary for a specific document."""
    try:
        document = document_usecase.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        summary = chat_usecase.create_document_summary(document)
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "summary": summary.summary,
            "key_topics": summary.key_topics,
            "created_time": summary.created_time.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
