"""Routes for GST filing workflow with date-based filtering."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from auth.dependencies import get_current_active_user
from schemas.simplified_schemas import UserDB
from agents.date_filtering_agent import DateFilteringAgent
from agents.gstr1_extraction_agent import GSTR1ExtractionAgent
from usecases.shared_instances import get_document_processing_agent
from typing import List, Dict, Any
from pydantic import BaseModel
import uuid

filing_router = APIRouter(prefix="/api/filing", tags=["filing"])

class FilingRequest(BaseModel):
    """Request model for filing submission."""
    document_ids: List[str]
    analysis_session_id: str
    filing_types: Dict[str, Dict[str, str]]  # {"GSTR-1": {"start_date": "2024-01-01", "end_date": "2024-01-31"}}

@filing_router.post("/submit")
async def submit_filing(
    filing_request: FilingRequest,
    current_user: UserDB = Depends(get_current_active_user)
):
    """Submit GST filing with date-based chunk filtering."""
    
    try:
        # Get document processing agent
        doc_agent = get_document_processing_agent()
        
        # Retrieve document chunks
        all_chunks = []
        
        # Always use all chunks from document store (document IDs are not stored by ID)
        from agents.document_processing_agent import document_store
        for filename, chunks in document_store["chunks"].items():
            if chunks:
                all_chunks.extend(chunks)
        
        # Log debug info
        print(f"Document store contents: {list(document_store['chunks'].keys())}")
        print(f"Total chunks found: {len(all_chunks)}")
        if filing_request.document_ids:
            print(f"Requested document IDs: {filing_request.document_ids}")
            print("Note: Using all available chunks instead of specific document IDs")
        
        if not all_chunks:
            raise HTTPException(status_code=404, detail="No document chunks found")
        
        # Use all chunks for GSTR-1 processing (categorization removed)
        gstr1_chunk_indices = list(range(len(all_chunks)))
        print(f"Processing all {len(gstr1_chunk_indices)} chunks for GSTR-1")
        
        filing_results = {}
        
        # Process GSTR-1 filing if requested
        if "GSTR-1" in filing_request.filing_types:
            gstr1_details = filing_request.filing_types.get("GSTR-1", {})
            # Only pass GSTR-1 categorized chunks
            gstr1_chunks = [all_chunks[i] for i in gstr1_chunk_indices if i < len(all_chunks)]
            gstr1_result = await process_gstr1_filing(
                gstr1_chunks,
                gstr1_details,
                current_user
            )
            filing_results["GSTR-1"] = gstr1_result
        
        # GSTR-2 is now auto-generated, no manual processing needed
        
        return {
            "filing_id": str(uuid.uuid4()),
            "status": "processing",
            "filing_types": filing_request.filing_types,
            "results": filing_results,
            "user_id": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filing submission failed: {str(e)}")

async def process_gstr1_filing(chunks: List[str], gstr1_details: Dict[str, str], user: UserDB) -> Dict[str, Any]:
    """Process GSTR-1 filing with date filtering."""
    
    try:
        # Step 1: Filter chunks by filing period
        try:
            date_agent = DateFilteringAgent()
            
            # Check if using custom date range or monthly filing
            if "start_date" in gstr1_details and "end_date" in gstr1_details:
                filtered_result = date_agent.filter_chunks_by_period(
                    chunks=chunks,
                    start_date=gstr1_details["start_date"],
                    end_date=gstr1_details["end_date"]
                )
            else:
                filtered_result = date_agent.filter_chunks_by_period(
                    chunks=chunks,
                    filing_month=gstr1_details.get("month"),
                    filing_year=gstr1_details.get("year")
                )
        except Exception as e:
            print(f"Date filtering error: {e}")
            # Fallback: use all chunks
            filtered_result = {
                "filtered_chunks": list(range(len(chunks))),
                "filing_period": "All chunks (fallback)",
                "total_original_chunks": len(chunks),
                "total_filtered_chunks": len(chunks),
                "notes": f"Date filtering failed, using all chunks: {str(e)}"
            }
        
        if "error" in filtered_result:
            return {"status": "error", "message": filtered_result["error"]}
        
        # Get filtered chunk indices
        filtered_indices = filtered_result["filtered_chunks"]
        if not filtered_indices:
            return {
                "status": "no_data",
                "message": f"No transactions found for the selected date period: {filtered_result['filing_period']}",
                "filing_period": filtered_result["filing_period"],
                "total_chunks_analyzed": filtered_result["total_original_chunks"],
                "error_type": "no_chunks_in_date_range"
            }
        
        # Step 2: Extract GSTR-1 data from filtered chunks
        filtered_chunks = [chunks[i] for i in filtered_indices if i < len(chunks)]
        
        print(f"Date filtering results:")
        print(f"- Original chunks: {len(chunks)}")
        print(f"- Filtered indices: {filtered_indices}")
        print(f"- Filtered chunks: {len(filtered_chunks)}")
        print(f"- Filing period: {filtered_result['filing_period']}")
        
        try:
            # Use GSTR-1 extraction agent to process filtered chunks
            import os
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            gstr1_agent = GSTR1ExtractionAgent(api_key=api_key)
            extraction_result = gstr1_agent.extract_gstr1_data(
                chunks=filtered_chunks,
                user_gstin=user.gstin,
                user_company_name=user.company_name
            )
            
            # Save GSTR-1 data to database
            await save_gstr1_to_database(
                extraction_result=extraction_result,
                filtered_result=filtered_result,
                gstr1_details=gstr1_details,
                user=user
            )
            
            # Add status and message for consistency
            extraction_result["status"] = "completed"
            extraction_result["message"] = f"Successfully processed {len(filtered_chunks)} chunks for GSTR-1 filing and saved to database"
            
            # Store filtered chunks info for report access
            extraction_result["filtered_chunks_info"] = {
                "total_original_chunks": len(chunks),
                "filtered_chunk_count": len(filtered_chunks),
                "filtered_indices": filtered_indices,
                "filing_period": filtered_result["filing_period"]
            }
            
        except Exception as e:
            print(f"GSTR-1 extraction error: {e}")
            # Fallback to basic result
            extraction_result = {
                "status": "completed",
                "total_invoices": len(filtered_chunks),
                "b2b_invoices": len(filtered_chunks),
                "total_taxable_value": 0.0,
                "total_tax_amount": 0.0,
                "message": f"Processed {len(filtered_chunks)} chunks (extraction failed: {str(e)})"
            }
        
        return {
            "status": "completed",
            "filing_period": filtered_result["filing_period"],
            "date_filtering": {
                "total_chunks_analyzed": filtered_result["total_original_chunks"],
                "filtered_chunks_count": filtered_result["total_filtered_chunks"],
                "notes": filtered_result.get("notes", "")
            },
            "gstr1_extraction": extraction_result,
            "user_id": user.id
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"GSTR-1 processing failed: {str(e)}"
        }

async def save_gstr1_to_database(extraction_result: Dict[str, Any], filtered_result: Dict[str, Any], gstr1_details: Dict[str, str], user: UserDB):
    """Save GSTR-1 extraction results to database."""
    
    try:
        from database.database import get_db
        from schemas.simplified_schemas import GSTR1ReturnDB
        from sqlalchemy.orm import Session
        import json
        import uuid
        from datetime import datetime
        
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # Create GSTR-1 return record
            return_id = str(uuid.uuid4())
            
            # Prepare JSON data in GSTR-1 format
            gstr1_formatted_data = {
                "gstr1_return": {
                    "header": {
                        "gstin": user.gstin,
                        "company_name": user.company_name,
                        "filing_period": filtered_result.get("filing_period", f"{gstr1_details.get('month', '')}{gstr1_details.get('year', '')}")
                    },
                    "invoices": extraction_result.get("invoices", []),
                    "summary": {
                        "total_invoices": extraction_result.get("total_invoices", 0),
                        "total_taxable_value": extraction_result.get("total_taxable_value", 0.0),
                        "total_tax": extraction_result.get("total_tax_amount", 0.0),
                        "total_invoice_value": sum(inv.get("invoice_value", 0) for inv in (extraction_result.get("invoices") or []))
                    }
                }
            }
            
            # Also store processing metadata
            json_data = {
                "gstr1_data": gstr1_formatted_data,
                "extraction_result": extraction_result,
                "date_filtering": {
                    "total_chunks_analyzed": filtered_result.get("total_original_chunks", 0),
                    "filtered_chunks_count": filtered_result.get("total_filtered_chunks", 0),
                    "notes": filtered_result.get("notes", "")
                },
                "filing_details": gstr1_details,
                "processed_at": datetime.now().isoformat()
            }
            
            gstr1_return = GSTR1ReturnDB(
                id=return_id,
                user_id=user.id,
                gstin=user.gstin,
                company_name=user.company_name,
                filing_period=filtered_result.get("filing_period", f"{gstr1_details.get('month', '')} {gstr1_details.get('year', '')}"),
                status="completed",
                total_invoices=extraction_result.get("total_invoices", 0),
                total_taxable_value=extraction_result.get("total_taxable_value", 0.0),
                total_tax=extraction_result.get("total_tax_amount", 0.0),
                json_data=json.dumps(json_data),
                created_at=datetime.now()
            )
            
            db.add(gstr1_return)
            
            # Note: Individual invoices and items are stored in JSON data
            # The simplified schema stores everything in the json_data field
            
            # Commit all changes
            db.commit()
            print(f"✅ GSTR-1 data saved to database with return ID: {return_id}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error saving GSTR-1 data to database: {e}")
        raise e

# GSTR-2 processing function removed - GSTR-2 is now auto-generated

@filing_router.get("/status/{filing_id}")
async def get_filing_status(
    filing_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status of a filing submission."""
    
    # Query database for filing results
    # For now, we'll check if there are any GSTR-1 returns for this user
    from schemas.simplified_schemas import GSTR1ReturnDB
    
    recent_return = db.query(GSTR1ReturnDB).filter(
        GSTR1ReturnDB.user_id == current_user.id
    ).order_by(GSTR1ReturnDB.created_at.desc()).first()
    
    if recent_return:
        # Parse the stored JSON data to get detailed results
        import json
        try:
            json_data = json.loads(recent_return.json_data) if recent_return.json_data else {}
        except:
            json_data = {}
        
        return {
            "filing_id": filing_id,
            "status": "completed",
            "filing_types": ["GSTR-1"],
            "results": {
                "GSTR-1": {
                    "status": recent_return.status,
                    "filing_period": recent_return.filing_period,
                    "date_filtering": {
                        "total_chunks_analyzed": json_data.get("total_chunks_analyzed", 0),
                        "filtered_chunks_count": json_data.get("filtered_chunks_count", 0),
                        "notes": json_data.get("date_filtering_notes", "")
                    },
                    "gstr1_extraction": {
                        "status": "completed",
                        "total_invoices": int(recent_return.total_invoices or 0),
                        "b2b_invoices": int(recent_return.total_invoices or 0),
                        "total_taxable_value": float(recent_return.total_taxable_value or 0),
                        "total_tax_amount": float(recent_return.total_tax or 0),
                        "message": f"Successfully processed {int(recent_return.total_invoices or 0)} invoices"
                    }
                }
            },
            "created_at": recent_return.created_at.isoformat() if recent_return.created_at else None,
            "user_id": current_user.id
        }
    else:
        # No filing found, return basic status
        return {
            "filing_id": filing_id,
            "status": "not_found",
            "message": "No filing results found for this user",
            "user_id": current_user.id
        }
