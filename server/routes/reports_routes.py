"""Routes for GSTR-1 reports and data visualization."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from auth.dependencies import get_current_active_user
from schemas.simplified_schemas import UserDB, GSTR1ReturnDB
from typing import List, Dict, Any
import json
from datetime import datetime

reports_router = APIRouter(prefix="/api/reports", tags=["reports"])

@reports_router.get("/gstr1/latest")
async def get_latest_gstr1_return(
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the latest GSTR-1 return for the current user."""
    
    try:
        # Get the most recent return for user
        latest_return = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.user_id == current_user.id
        ).order_by(GSTR1ReturnDB.created_at.desc()).first()
        
        if not latest_return:
            return {
                "status": "not_found",
                "message": "No GSTR-1 returns found for this user"
            }
        
        # Parse JSON data for additional details
        json_data = {}
        if latest_return.json_data:
            try:
                json_data = json.loads(latest_return.json_data)
            except:
                pass
        
        # Extract invoice details from JSON
        extraction_result = json_data.get("extraction_result", {})
        invoices_data = extraction_result.get("invoices", [])
        
        # Extract categorized data that frontend expects
        b2b_data = extraction_result.get("b2b", [])
        b2cl_data = extraction_result.get("b2cl", [])
        b2cs_data = extraction_result.get("b2cs", [])
        
        return {
            "filing_id": latest_return.id,
            "status": "completed",
            "filing_types": ["GSTR-1"],
            "results": {
                "GSTR-1": {
                    "status": latest_return.status,
                    "filing_period": latest_return.filing_period,
                    "date_filtering": json_data.get("date_filtering", {}),
                    "gstr1_extraction": {
                        "status": "completed",
                        "total_invoices": int(latest_return.total_invoices or 0),
                        "b2b_invoices": extraction_result.get("b2b_invoices", 0),
                        "b2cl_invoices": extraction_result.get("b2cl_invoices", 0),
                        "b2cs_invoices": extraction_result.get("b2cs_invoices", 0),
                        "total_taxable_value": float(latest_return.total_taxable_value or 0),
                        "total_tax_amount": float(latest_return.total_tax or 0),
                        "invoices": invoices_data,
                        "b2b": b2b_data,
                        "b2cl": b2cl_data,
                        "b2cs": b2cs_data,
                        "message": f"Successfully processed {int(latest_return.total_invoices or 0)} invoices"
                    }
                }
            },
            "created_at": latest_return.created_at.isoformat() if latest_return.created_at else None,
            "user_id": current_user.id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest GSTR-1 return: {str(e)}")

@reports_router.get("/gstr1/returns")
async def get_gstr1_returns(
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all GSTR-1 returns for the current user."""
    
    try:
        returns = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.user_id == current_user.id
        ).order_by(GSTR1ReturnDB.created_at.desc()).all()
        
        return {
            "total_returns": len(returns),
            "returns": [
                {
                    "id": return_record.id,
                    "filing_period": return_record.filing_period,
                    "status": return_record.status,
                    "total_invoices": return_record.total_invoices,
                    "total_taxable_value": float(return_record.total_taxable_value or 0),
                    "total_tax": float(return_record.total_tax or 0),
                    "created_at": return_record.created_at.isoformat() if return_record.created_at else None
                }
                for return_record in returns
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch GSTR-1 returns: {str(e)}")

@reports_router.get("/gstr1/returns/{return_id}")
async def get_gstr1_return_details(
    return_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed GSTR-1 return data from JSON storage."""
    
    try:
        # Get the return record
        return_record = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.id == return_id,
            GSTR1ReturnDB.user_id == current_user.id
        ).first()
        
        if not return_record:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        # Parse JSON data for detailed information
        json_data = {}
        if return_record.json_data:
            try:
                json_data = json.loads(return_record.json_data)
            except:
                pass
        
        # Extract invoice details from JSON
        extraction_result = json_data.get("extraction_result", {})
        invoices_data = extraction_result.get("invoices", [])
        
        return {
            "return_details": {
                "id": return_record.id,
                "filing_period": return_record.filing_period,
                "status": return_record.status,
                "total_invoices": return_record.total_invoices,
                "total_taxable_value": float(return_record.total_taxable_value or 0),
                "total_tax": float(return_record.total_tax or 0),
                "created_at": return_record.created_at.isoformat() if return_record.created_at else None
            },
            "summary": {
                "total_b2b_invoices": extraction_result.get("b2b_invoices", 0),
                "total_b2c_invoices": extraction_result.get("b2c_invoices", 0),
                "total_taxable_value": float(extraction_result.get("total_taxable_value", 0)),
                "total_cgst": float(extraction_result.get("total_cgst", 0)),
                "total_sgst": float(extraction_result.get("total_sgst", 0)),
                "total_igst": float(extraction_result.get("total_igst", 0)),
                "total_tax": float(extraction_result.get("total_tax_amount", 0)),
                "total_invoice_value": float(extraction_result.get("total_invoice_value", 0))
            },
            "invoices": invoices_data,
            "processing_details": {
                "date_filtering": json_data.get("date_filtering", {}),
                "filing_details": json_data.get("filing_details", {}),
                "processed_at": json_data.get("processed_at", "")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {"error": "Failed to get GSTR-1 return details", "details": str(e)}

@reports_router.get("/gstr1/returns/{return_id}/download")
async def download_gstr1_json(
    return_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download GSTR-1 return as JSON file."""
    
    try:
        # Get the return record
        return_record = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.id == return_id,
            GSTR1ReturnDB.user_id == current_user.id
        ).first()
        
        if not return_record:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        # Parse JSON data to get invoice details
        json_data = {}
        if return_record.json_data:
            try:
                json_data = json.loads(return_record.json_data)
            except:
                pass
        
        # Extract invoice data from stored JSON
        extraction_result = json_data.get("extraction_result", {})
        invoices_data = extraction_result.get("invoices", [])
        
        # Extract GSTR-1 formatted data from stored JSON
        gstr1_json = json_data.get("gstr1_data", {})
        
        # Fallback to building structure if not found
        if not gstr1_json:
            extraction_result = json_data.get("extraction_result", {})
            gstr1_json = {
                "gstr1_return": {
                    "header": {
                        "gstin": current_user.gstin,
                        "company_name": current_user.company_name,
                        "filing_period": return_record.filing_period,
                        "generated_at": return_record.created_at.isoformat() if return_record.created_at else None
                    },
                    "invoices": extraction_result.get("invoices", []),
                    "summary": {
                        "total_invoices": return_record.total_invoices,
                        "total_taxable_value": float(return_record.total_taxable_value or 0),
                        "total_tax": float(return_record.total_tax or 0),
                        "total_invoice_value": sum(inv.get("invoice_value", 0) for inv in extraction_result.get("invoices", []))
                    }
                }
            }
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=gstr1_json,
            headers={
                "Content-Disposition": f"attachment; filename=GSTR1_{return_record.filing_period.replace(' ', '_')}.json"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate GSTR-1 JSON: {str(e)}")
