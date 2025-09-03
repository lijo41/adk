"""GSTR-1 API routes."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from database.database import get_db
from schemas.simplified_schemas import UserDB, GSTR1ReturnDB
from auth.dependencies import get_current_active_user
from usecases.shared_instances import gstr1_usecase
from models.api_requests import GSTR1CreateRequest, B2BItemRequest, B2BInvoiceRequest

# Load environment
load_dotenv()

gstr1_router = APIRouter(prefix="/api/gstr1", tags=["gstr1"])


@gstr1_router.post("/create")
async def create_gstr1_return(
    request: GSTR1CreateRequest,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new GSTR-1 return."""
    try:
        # Create new GSTR-1 return in simplified database
        db_return = GSTR1ReturnDB(
            user_id=current_user.id,
            gstin=current_user.gstin,
            company_name=current_user.company_name,
            filing_period=request.filing_period,
            gross_turnover=Decimal(str(request.gross_turnover))
        )
        
        db.add(db_return)
        db.commit()
        db.refresh(db_return)
        
        return {
            "return_id": db_return.id,
            "gstin": db_return.gstin,
            "company_name": db_return.company_name,
            "filing_period": db_return.filing_period,
            "status": db_return.status,
            "created_at": db_return.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.get("/{return_id}/table")
async def get_gstr1_table_data(
    return_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get GSTR-1 data in table format for UI display."""
    try:
        # Get GSTR-1 return from database
        db_return = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.id == return_id,
            GSTR1ReturnDB.user_id == current_user.id
        ).first()
        
        if not db_return:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        # Parse JSON data if available
        invoices = []
        summary = {}
        if db_return.json_data:
            import json
            json_data = json.loads(db_return.json_data)
            invoices = json_data.get("gstr1_return", {}).get("invoices", [])
            summary = json_data.get("gstr1_return", {}).get("summary", {})
        
        # Format for table display
        table_data = {
            "header": {
                "gstin": db_return.gstin,
                "company_name": db_return.company_name,
                "filing_period": db_return.filing_period,
                "status": db_return.status
            },
            "invoices": invoices,
            "summary": summary,
            "invoice_count": len(invoices)
        }
        
        return table_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.get("/{return_id}/json")
async def generate_gstr1_json(
    return_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate GSTR-1 JSON for a return."""
    try:
        # Get GSTR-1 return from database
        db_return = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.id == return_id,
            GSTR1ReturnDB.user_id == current_user.id
        ).first()
        
        if not db_return:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        # Return stored JSON data or empty structure
        if db_return.json_data:
            import json
            return json.loads(db_return.json_data)
        else:
            return {
                "gstr1_return": {
                    "header": {
                        "gstin": db_return.gstin,
                        "company_name": db_return.company_name,
                        "filing_period": db_return.filing_period
                    },
                    "invoices": [],
                    "summary": {}
                }
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.post("/{return_id}/save")
async def save_gstr1_return(
    return_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save GSTR-1 return to storage."""
    try:
        # Get GSTR-1 return from database
        db_return = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.id == return_id,
            GSTR1ReturnDB.user_id == current_user.id
        ).first()
        
        if not db_return:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        # Update status to saved
        db_return.status = "saved"
        db.commit()
        
        return {
            "message": "GSTR-1 return saved successfully",
            "return_id": return_id,
            "status": db_return.status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.get("/list")
async def list_gstr1_returns(
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all GSTR-1 returns."""
    try:
        # Get all GSTR-1 returns for current user
        db_returns = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.user_id == current_user.id
        ).order_by(GSTR1ReturnDB.created_at.desc()).all()
        
        returns = []
        for db_return in db_returns:
            returns.append({
                "return_id": db_return.id,
                "gstin": db_return.gstin,
                "company_name": db_return.company_name,
                "filing_period": db_return.filing_period,
                "status": db_return.status,
                "total_invoices": int(db_return.total_invoices or 0),
                "total_invoice_value": float(db_return.total_invoice_value or 0),
                "created_at": db_return.created_at.isoformat()
            })
        
        return {
            "returns": returns,
            "count": len(returns)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@gstr1_router.get("/{return_id}")
async def get_gstr1_return(
    return_id: str,
    current_user: UserDB = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get GSTR-1 return details."""
    try:
        # Get GSTR-1 return from database
        db_return = db.query(GSTR1ReturnDB).filter(
            GSTR1ReturnDB.id == return_id,
            GSTR1ReturnDB.user_id == current_user.id
        ).first()
        
        if not db_return:
            raise HTTPException(status_code=404, detail="GSTR-1 return not found")
        
        return {
            "return_id": db_return.id,
            "header": {
                "gstin": db_return.gstin,
                "company_name": db_return.company_name,
                "filing_period": db_return.filing_period,
                "gross_turnover": float(db_return.gross_turnover or 0),
                "status": db_return.status
            },
            "total_invoices": int(db_return.total_invoices or 0),
            "total_taxable_value": float(db_return.total_taxable_value or 0),
            "total_tax": float(db_return.total_tax or 0),
            "total_invoice_value": float(db_return.total_invoice_value or 0),
            "created_at": db_return.created_at.isoformat(),
            "updated_at": db_return.updated_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
