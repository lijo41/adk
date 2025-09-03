"""Routes for document categorization and smart analysis."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from auth.dependencies import get_current_active_user
from schemas.simplified_schemas import UserDB
from agents.categorization_agent import CategorizationAgent
from usecases.shared_instances import get_document_processing_agent
from typing import List, Dict, Any
import uuid

categorization_router = APIRouter(prefix="/api/categorization", tags=["categorization"])

from pydantic import BaseModel

class AnalyzeRequest(BaseModel):
    document_ids: List[str] = []

@categorization_router.post("/analyze")
async def analyze_documents(
    request: AnalyzeRequest,
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Analyze uploaded documents and categorize them for GSTR-1 and GSTR-2 filing.
    
    Args:
        document_ids: List of document IDs to analyze
        current_user: Current authenticated user
        
    Returns:
        Categorization analysis results
    """
    try:
        # Get document processing agent to retrieve actual chunks
        doc_agent = get_document_processing_agent()
        categorization_agent = CategorizationAgent()
        
        # Get actual document chunks from document processing agent
        from agents.document_processing_agent import document_store
        
        # Retrieve chunks from all processed documents with source tracking
        all_chunks = []
        chunk_metadata = []  # Track which document each chunk came from
        processed_docs = []
        
        for filename, chunks in document_store["chunks"].items():
            if chunks:  # Only include documents that have been processed and chunked
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    chunk_metadata.append({
                        "source_document": filename,
                        "chunk_index_in_doc": i,
                        "global_chunk_index": len(all_chunks) - 1
                    })
                processed_docs.append(filename)
        
        # If no processed documents found, use fallback
        if not all_chunks:
            all_chunks = [
                "No processed documents found. Please upload and process documents first.",
                "Sample GST invoice data for demonstration purposes.",
                "Mock B2B transaction: Invoice #INV001, Amount: ₹10,000, GSTIN: 29ABCDE1234F1Z5"
            ]
        
        # Perform categorization analysis on actual chunks
        categorization_result = categorization_agent.categorize_chunks(all_chunks)
        
        # Add chunk source mapping to results
        categorization_result["chunk_metadata"] = chunk_metadata
        
        # Create per-document breakdown
        doc_breakdown = {}
        for doc in processed_docs:
            doc_breakdown[doc] = {
                "gstr1_chunks": [],
                "gstr2_chunks": [],
                "irrelevant_chunks": [],
                "total_chunks": 0
            }
        
        # Map categorized chunks back to their source documents
        chunk_categorizations = categorization_result.get("chunk_categorization", [])
        for i, categorization in enumerate(chunk_categorizations):
            if i < len(chunk_metadata):
                source_doc = chunk_metadata[i]["source_document"]
                category = categorization.get("category", "irrelevant")
                
                doc_breakdown[source_doc]["total_chunks"] += 1
                
                if category == "gstr1":
                    doc_breakdown[source_doc]["gstr1_chunks"].append(i)
                elif category == "gstr2":
                    doc_breakdown[source_doc]["gstr2_chunks"].append(i)
                else:
                    doc_breakdown[source_doc]["irrelevant_chunks"].append(i)
        
        categorization_result["document_breakdown"] = doc_breakdown
        
        return {
            "status": "success",
            "processed_documents": processed_docs,
            "total_chunks": len(all_chunks),
            "categorization": categorization_result,
            "session_id": str(uuid.uuid4()),
            "user_id": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@categorization_router.get("/analysis/{session_id}")
async def get_analysis_results(
    session_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Get previously performed analysis results.
    
    Args:
        session_id: Analysis session ID
        current_user: Current authenticated user
        
    Returns:
        Stored analysis results
    """
    # In a real implementation, you would retrieve from database
    # For now, return a sample result
    return {
        "session_id": session_id,
        "status": "completed",
        "gstr1_analysis": {
            "relevant_chunks": [0, 1, 2],
            "b2b_invoices_count": 45,
            "b2c_invoices_count": 12,
            "export_invoices_count": 3,
            "total_transactions": 60
        },
        "gstr2_analysis": {
            "relevant_chunks": [3, 4],
            "purchase_invoices_count": 38,
            "import_invoices_count": 5,
            "total_transactions": 43
        },
        "recommendations": {
            "suggested_filings": ["GSTR1", "GSTR2"],
            "confidence_score": 0.92,
            "notes": "Both GSTR-1 and GSTR-2 data detected with high confidence"
        }
    }

@categorization_router.post("/process-filing")
async def process_filing(
    filing_request: Dict[str, Any],
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Process the selected filing types based on categorization results.
    
    Args:
        filing_request: Contains session_id, selected_filings, and filing_details
        current_user: Current authenticated user
        
    Returns:
        Processing status and results
    """
    try:
        session_id = filing_request.get("session_id")
        selected_filings = filing_request.get("selected_filings", [])
        filing_details = filing_request.get("filing_details", {})
        
        # Simulate processing steps
        processing_steps = [
            {"step": "document_parsing", "status": "completed", "progress": 20},
            {"step": "data_extraction", "status": "completed", "progress": 40},
            {"step": "gstr1_generation", "status": "in_progress", "progress": 60},
            {"step": "gstr2_generation", "status": "pending", "progress": 80},
            {"step": "compliance_check", "status": "pending", "progress": 100}
        ]
        
        return {
            "session_id": session_id,
            "processing_id": str(uuid.uuid4()),
            "status": "processing",
            "selected_filings": selected_filings,
            "filing_details": filing_details,
            "steps": processing_steps,
            "overall_progress": 60,
            "estimated_completion": "2-3 minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@categorization_router.get("/processing-status/{processing_id}")
async def get_processing_status(
    processing_id: str,
    current_user: UserDB = Depends(get_current_active_user)
):
    """
    Get the current status of filing processing.
    
    Args:
        processing_id: Processing session ID
        current_user: Current authenticated user
        
    Returns:
        Current processing status
    """
    # Simulate different processing states
    import random
    progress = min(100, random.randint(75, 100))
    
    steps = [
        {"step": "document_parsing", "status": "completed", "progress": 20},
        {"step": "data_extraction", "status": "completed", "progress": 40},
        {"step": "gstr1_generation", "status": "completed", "progress": 60},
        {"step": "gstr2_generation", "status": "completed" if progress > 80 else "in_progress", "progress": 80},
        {"step": "compliance_check", "status": "completed" if progress == 100 else "pending", "progress": 100}
    ]
    
    return {
        "processing_id": processing_id,
        "status": "completed" if progress == 100 else "processing",
        "overall_progress": progress,
        "steps": steps,
        "current_step": "compliance_check" if progress > 80 else "gstr2_generation",
        "estimated_completion": "30 seconds" if progress > 90 else "1-2 minutes"
    }
